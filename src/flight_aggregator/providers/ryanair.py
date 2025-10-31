from __future__ import annotations
import asyncio, httpx, datetime as dt
from typing import List, Dict
from .base import Fare, Provider

# Unofficial endpoints. Subject to change.
# We use oneWayFares to discover cheapest per day+destination.
BASE = "https://www.ryanair.com/api/farfnd/3/oneWayFares"

class RyanairProvider(Provider):
    name = "ryanair"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout

    async def _search_day(self, client: httpx.AsyncClient, origin: str, day: str, currency: str) -> List[Fare]:
        params = {
            "departureAirportIataCode": origin,
            "dateOut": day,
            "currency": currency,
            "market": "en-us"
        }
        r = await client.get(BASE, params=params)
        r.raise_for_status()
        data = r.json()
        fares: List[Fare] = []
        for item in data.get("fares", []):
            trip = item.get("outbound", {})
            arrival = trip.get("arrivalAirport", {}).get("iataCode")
            price_info = trip.get("price", {})
            price = price_info.get("value")
            if arrival and price is not None:
                fares.append(Fare(
                    date=day,
                    destination=arrival,
                    provider=self.name,
                    price=float(price),
                    currency=price_info.get("currencyCode", currency),
                    flight_number=None,
                    booking_url=None,
                    raw=item
                ))
        return fares

    async def search(self, origin: str, dates: List[str], currency: str = "EUR") -> List[Fare]:
        fares: List[Fare] = []
        limits = httpx.Limits(max_connections=6)
        async with httpx.AsyncClient(timeout=self.timeout, limits=limits, headers={"Accept": "application/json"}) as client:
            tasks = [self._search_day(client, origin, d, currency) for d in dates]
            for coro in asyncio.as_completed(tasks):
                try:
                    fares.extend(await coro)
                except Exception:
                    continue
        return fares
