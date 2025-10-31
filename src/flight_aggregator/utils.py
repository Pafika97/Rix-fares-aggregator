from __future__ import annotations
import os, asyncio, datetime as dt
from typing import List
from dataclasses import dataclass

def date_range(days_ahead: int, start_date: str | None = None) -> List[str]:
    if start_date:
        start = dt.date.fromisoformat(start_date)
    else:
        start = dt.date.today()
    return [(start + dt.timedelta(days=i)).isoformat() for i in range(days_ahead)]

@dataclass
class Options:
    origin: str = "RIX"
    days: int = 60
    currency: str = os.getenv("DEFAULT_CURRENCY", "EUR")
    providers: List[str] = None
    out_csv: str | None = "flights.csv"
    out_xlsx: str | None = None
    timeout: int = 25
    concurrency: int = 8
    max_per_day: int = 1
    verbose: bool = False
