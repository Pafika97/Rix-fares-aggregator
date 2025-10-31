from __future__ import annotations
import asyncio, httpx
from typing import List
from .base import Fare, Provider

# Unofficial Wizz endpoint (may change). Best-effort parsing.
# This endpoint returns 'cheap flights from origin' by month/day when available.
WIZZ_CHEAP = "https://be.wizzair.com/16.1.0/Api/search/cheapFlights"

class WizzProvider(Provider):
    name = "wizz"

    def __init__(self, timeout: int = 25):
        self.timeout = timeout

    async def _search_day(self, client: httpx.AsyncClient, origin: str, day: str, currency: str) -> List[Fare]:
        # The 'cheapFlights' endpoint often wants month granularity; we still filter client-side for exact day.
        params = {"departureIata": origin, "priceType": "regular", "currencyCode": currency}
        r = await client.get(WIZZ_CHEAP, params=params)
        r.raise_for_status()
        data = r.json()
        fares: List[Fare] = []
        for route in data.get("cheapFlightList", []):
            if route.get("departureStation") != origin:
                continue
            for offer in route.get("prices", []):
                if offer.get("date") == day:
                    destination = route.get("arrivalStation")
                    price = offer.get("price")
                    if destination and price is not None:
                        fares.append(Fare(
                            date=day,
                            destination=destination,
                            provider=self.name,
                            price=float(price),
                            currency=currency,
                            flight_number=None,
                            booking_url=None,
                            raw=offer
                        ))
        return fares

    async def search(self, origin: str, dates: List[str], currency: str = "EUR") -> List[Fare]:
        fares: List[Fare] = []
        limits = httpx.Limits(max_connections=4)
        async with httpx.AsyncClient(timeout=self.timeout, limits=limits) as client:
            tasks = [self._search_day(client, origin, d, currency) for d in dates]
            for coro in asyncio.as_completed(tasks):
                try:
                    fares.extend(await coro)
                except Exception:
                    continue
        return fares
