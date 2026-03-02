from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
from datetime import datetime, timedelta
from typing import Any
import os

app = FastAPI(title="API Dashboard", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Cache to avoid hitting APIs too frequently
cache: dict[str, tuple[Any, datetime]] = {}
CACHE_DURATION = timedelta(minutes=5)


def get_from_cache(key: str) -> Any | None:
    if key in cache:
        data, timestamp = cache[key]
        if datetime.now() - timestamp < CACHE_DURATION:
            return data
    return None


def set_cache(key: str, data: Any) -> None:
    cache[key] = (data, datetime.now())


@app.get("/")
async def index():
    return FileResponse("api_dashboard_frontend.html")


@app.get("/api/weather/{city}")
async def get_weather(city: str):
    cached = get_from_cache(f"weather_{city}")
    if cached:
        return cached

    API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            result = {
                "success": True,
                "city": data["name"],
                "temperature": round(data["main"]["temp"]),
                "description": data["weather"][0]["description"],
                "icon": data["weather"][0]["icon"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"],
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache(f"weather_{city}", result)
    return result


@app.get("/api/joke")
async def get_joke():
    """Always fetches a fresh joke — no caching."""
    url = "https://v2.jokeapi.dev/joke/Programming?type=single"
    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return {"success": True, "joke": data.get("joke", "No joke available")}
        except Exception as e:
            return {"success": False, "error": str(e)}


@app.get("/api/nasa")
async def get_nasa_apod():
    cached = get_from_cache("nasa_apod")
    if cached:
        return cached

    API_KEY = os.getenv("NASA_API_KEY", "DEMO_KEY")
    url = f"https://api.nasa.gov/planetary/apod?api_key={API_KEY}"

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            result = {
                "success": True,
                "title": data["title"],
                "date": data["date"],
                "explanation": data["explanation"],
                "url": data["url"],
                "media_type": data.get("media_type", "image"),
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache("nasa_apod", result)
    return result


@app.get("/api/crypto")
async def get_crypto():
    cached = get_from_cache("crypto")
    if cached:
        return cached

    url = (
        "https://api.coingecko.com/api/v3/simple/price"
        "?ids=bitcoin,ethereum,cardano&vs_currencies=usd&include_24hr_change=true"
    )

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            result = {
                "success": True,
                "bitcoin": {
                    "price": data["bitcoin"]["usd"],
                    "change": round(data["bitcoin"]["usd_24h_change"], 2),
                },
                "ethereum": {
                    "price": data["ethereum"]["usd"],
                    "change": round(data["ethereum"]["usd_24h_change"], 2),
                },
                "cardano": {
                    "price": data["cardano"]["usd"],
                    "change": round(data["cardano"]["usd_24h_change"], 2),
                },
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache("crypto", result)
    return result


@app.get("/api/quote")
async def get_quote():
    """Fetch an inspirational quote of the day from ZenQuotes."""
    cached = get_from_cache("quote")
    if cached:
        return cached

    url = "https://zenquotes.io/api/today"

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            result = {
                "success": True,
                "quote": data[0]["q"],
                "author": data[0]["a"],
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache("quote", result)
    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_dashboard_backend:app", host="0.0.0.0", port=8000, reload=True)

# Run with: uv run uvicorn api_dashboard_backend:app --reload
