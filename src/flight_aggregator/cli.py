from __future__ import annotations
import argparse, asyncio, os, sys
from typing import List, Dict, Tuple
import pandas as pd
from .providers.base import Fare
from .providers.kiwi import KiwiProvider
from .providers.ryanair import RyanairProvider
from .providers.wizz import WizzProvider
# from .providers.amadeus import AmadeusProvider
from .utils import date_range, Options

PROVIDERS = {
    "kiwi": KiwiProvider,
    "ryanair": RyanairProvider,
    "wizz": WizzProvider,
    # "amadeus": AmadeusProvider,  # Placeholder
}

def parse_args() -> Options:
    p = argparse.ArgumentParser(description="Aggregate fares from RIX for the next N days into a table.")
    p.add_argument("--origin", default="RIX")
    p.add_argument("--days", type=int, default=60)
    p.add_argument("--currency", default=os.getenv("DEFAULT_CURRENCY", "EUR"))
    p.add_argument("--providers", default="kiwi,ryanair,wizz")
    p.add_argument("--out", dest="out_csv", default="flights.csv")
    p.add_argument("--excel", dest="out_xlsx", default=None)
    p.add_argument("--timeout", type=int, default=25)
    p.add_argument("--concurrency", type=int, default=8)
    p.add_argument("--max-per-day", type=int, default=1)
    p.add_argument("--verbose", action="store_true")
    a = p.parse_args()

    providers = [s.strip().lower() for s in a.providers.split(",") if s.strip()]
    return Options(
        origin=a.origin.upper(),
        days=a.days,
        currency=a.currency.upper(),
        providers=providers,
        out_csv=a.out_csv,
        out_xlsx=a.out_xlsx,
        timeout=a.timeout,
        concurrency=a.concurrency,
        max_per_day=a.max_per_day,
        verbose=a.verbose,
    )

async def run(opts: Options):
    dates = date_range(opts.days)
    providers = []
    for p in opts.providers:
        cls = PROVIDERS.get(p)
        if not cls:
            continue
        try:
            providers.append(cls(timeout=opts.timeout))
        except TypeError:
            providers.append(cls())

    async def gather_provider(provider) -> List[Fare]:
        try:
            return await provider.search(opts.origin, dates, currency=opts.currency)
        except Exception as e:
            if opts.verbose:
                print(f"[warn] provider {provider.name} failed: {e}", file=sys.stderr)
            return []

    results: List[Fare] = []
    tasks = [gather_provider(p) for p in providers]
    for coro in asyncio.as_completed(tasks):
        results.extend(await coro)

    if not results:
        print("No data returned. Check your API keys or try different providers.", file=sys.stderr)
        return

    # Build DataFrame
    rows = [r.model_dump() for r in results]
    df = pd.DataFrame(rows)

    # Normalize and keep cheapest per (date,destination,provider)
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    df = df.dropna(subset=["price", "date", "destination"])

    # Keep cheapest per (date, destination)
    df = df.sort_values(["date", "destination", "price"]).groupby(["date", "destination"], as_index=False).head(opts.max_per_day)

    # Sort output by date, price
    df = df.sort_values(["date", "price"]).reset_index(drop=True)

    # Save
    if opts.out_csv:
        df.to_csv(opts.out_csv, index=False, encoding="utf-8")
        print(f"Saved CSV -> {opts.out_csv}")
    if opts.out_xlsx:
        df.to_excel(opts.out_xlsx, index=False)
        print(f"Saved Excel -> {opts.out_xlsx}")

def main():
    opts = parse_args()
    asyncio.run(run(opts))

if __name__ == "__main__":
    main()
