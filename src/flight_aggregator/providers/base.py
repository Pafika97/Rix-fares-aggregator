from __future__ import annotations
from typing import List, Dict, Any
from pydantic import BaseModel

class Fare(BaseModel):
    date: str            # YYYY-MM-DD (origin local)
    destination: str     # IATA
    provider: str
    price: float
    currency: str
    flight_number: str | None = None
    booking_url: str | None = None
    raw: Dict[str, Any] | None = None

class Provider:
    name: str = "base"

    async def search(self, origin: str, dates: List[str], currency: str = "EUR") -> List[Fare]:
        raise NotImplementedError
