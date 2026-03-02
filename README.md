# API Dashboard

A personal dashboard that aggregates data from several free public APIs into a single-page interface. Built with **FastAPI** (async) on the backend and vanilla HTML/JS on the frontend.

## Features

| Card | API | Cached |
|---|---|---|
| Weather | OpenWeatherMap | Yes (5 min) |
| Crypto Prices | CoinGecko | Yes (5 min) |
| Programming Joke | JokeAPI | No |
| NASA Picture of the Day | NASA APOD | Yes (5 min) |
| Quote of the Day | ZenQuotes | Yes (5 min) |

## Requirements

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
# Clone the repo
git clone <repo-url>
cd api-dashboard

# Install dependencies
uv sync
```

## Configuration

The weather and NASA endpoints use API keys. Set them as environment variables before running:

```bash
export OPENWEATHER_API_KEY=your_key_here   # https://openweathermap.org/api
export NASA_API_KEY=your_key_here          # https://api.nasa.gov
```

Both fall back to placeholder/demo keys if unset — NASA's `DEMO_KEY` works but is rate-limited.

## Running

```bash
uv run uvicorn api_dashboard.main:app --reload
```

Then open [http://localhost:8000](http://localhost:8000) in your browser.

The interactive API docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Project Structure

```
api-dashboard/
├── api_dashboard/
│   ├── __init__.py
│   └── main.py                 # FastAPI app
├── api_dashboard_backend.py    # Backwards-compatibility shim
├── api_dashboard_frontend.html # Single-page frontend
├── pyproject.toml              # Project metadata and dependencies
└── .gitignore
```
