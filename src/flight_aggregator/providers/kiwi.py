from __future__ import annotations
import os, asyncio, httpx, datetime as dt
from typing import List
from .base import Fare, Provider

TEQUILA_URL = "https://api.tequila.kiwi.com"

class KiwiProvider(Provider):
    name = "kiwi"

    def __init__(self, api_key: str | None = None, timeout: int = 25):
        self.api_key = api_key or os.getenv("TEQUILA_API_KEY")
        self.timeout = timeout

    async def _search_day(self, client: httpx.AsyncClient, origin: str, day: str, currency: str) -> List[Fare]:
        # We query day->day (inclusive), returning cheapest per destination
        params = {
            "fly_from": origin,
            "date_from": day,
            "date_to": day,
            "curr": currency,
            "limit": 500,
            "sort": "price",
        }
        headers = {"apikey": self.api_key} if self.api_key else {}
        r = await client.get(f"{TEQUILA_URL}/v2/search", params=params, headers=headers)
        r.raise_for_status()
        data = r.json()
        fares: dict[str, Fare] = {}
        for item in data.get("data", []):
            dest = item.get("cityTo") or item.get("flyTo")
            price = float(item.get("price", 0.0))
            # Compose minimal flight id
            route = item.get("route", [])
            flight_number = None
            if route:
                seg = route[0]
                flight_number = f"{seg.get('airline','')}{seg.get('flight_no','')}"
            booking_url = item.get("deep_link")
            existing = fares.get(dest)
            if existing is None or price < existing.price:
                fares[dest] = Fare(
                    date=day,
                    destination=item.get("flyTo", dest),
                    provider=self.name,
                    price=price,
                    currency=currency,
                    flight_number=flight_number,
                    booking_url=booking_url,
                    raw=item,
                )
        return list(fares.values())

    async def search(self, origin: str, dates: List[str], currency: str = "EUR") -> List[Fare]:
        if not self.api_key:
            return []
        fares: List[Fare] = []
        limits = httpx.Limits(max_connections=8)
        async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as client:
            tasks = [self._search_day(client, origin, d, currency) for d in dates]
            for coro in asyncio.as_completed(tasks):
                try:
                    fares.extend(await coro)
                except Exception:
                    continue
        return fares
