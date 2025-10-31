# RIX Fares Aggregator

Fetch a **table of available airfares from Riga (RIX)** for the next N days across multiple sources
(Kiwi/Tequila, Ryanair, Wizz Air, optional Amadeus) and export to CSV and/or Excel.

## Highlights
- Async fetching (fast)
- Per-day scan for the next N days (default 60)
- Deduped by (date, destination) picking the cheapest price per provider
- Resilient: providers can fail without breaking the run
- Clean CLI

> **Note:** Google Flights, Skyscanner, Expedia do not have open public APIs suitable for scraping. Use Kiwi (Tequila) or Amadeus APIs (or airline public endpoints) for reliable programmatic data.

## Quick start

1) **Install Python 3.10+** and Git.
2) Create a virtualenv and install deps:
```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
3) Copy `.env.example` to `.env` and fill what you have:
   - `TEQUILA_API_KEY` (recommended) → https://tequila.kiwi.com/portal/login
   - `AMADEUS_CLIENT_ID`, `AMADEUS_CLIENT_SECRET` (optional) → https://developers.amadeus.com/
   - No keys needed for Ryanair/Wizz, but endpoints can change; the code is best-effort.

4) Run:
```bash
python -m flight_aggregator.cli --origin RIX --days 60 --out flights.csv --excel flights.xlsx
```

## CLI options
```
--origin RIX              IATA origin (default: RIX)
--days 60                 How many days ahead to scan (default: 60)
--currency EUR            Output currency (default: EUR)
--providers               Comma-separated providers. Default: kiwi,ryanair,wizz,amadeus
--out flights.csv         CSV output path
--excel flights.xlsx      Excel output path (optional)
--max-per-day 1           Keep N cheapest rows per (date,destination). Default 1
--timeout 25              HTTP timeout seconds per request (default 25)
--concurrency 8           Number of in-flight HTTP requests (default 8)
--verbose                 Extra logs
```
## Output columns
- `date` (YYYY-MM-DD)
- `destination` (IATA)
- `provider` (kiwi | ryanair | wizz | amadeus)
- `price` (numeric)
- `currency` (ISO code)
- `flight_number` (when available)
- `booking_url` (when available)

## Legal / ToS
Always comply with each provider's Terms of Service and rate limits. Prefer official APIs (Tequila/Amadeus).
The airline endpoints (Ryanair, Wizz) are **public but unofficial** and may change or block heavy use.

