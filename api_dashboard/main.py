from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import httpx
from datetime import datetime, timedelta
from typing import Any
from pathlib import Path
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

FRONTEND_FILE = Path(__file__).parent.parent / "api_dashboard_frontend.html"


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
    return FileResponse(FRONTEND_FILE)


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


AQI_LABELS = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
AQI_COLORS = {1: "#27ae60", 2: "#a8d627", 3: "#f39c12", 4: "#e67e22", 5: "#e74c3c"}


@app.get("/api/air-quality/{city}")
async def get_air_quality(city: str):
    cached = get_from_cache(f"air_quality_{city}")
    if cached:
        return cached

    API_KEY = os.getenv("OPENWEATHER_API_KEY", "YOUR_API_KEY_HERE")

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            # Geocode city to lat/lon
            geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={API_KEY}"
            geo_response = await client.get(geo_url)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            if not geo_data:
                return {"success": False, "error": f"City '{city}' not found"}
            lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

            # Fetch air pollution data
            aq_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={API_KEY}"
            aq_response = await client.get(aq_url)
            aq_response.raise_for_status()
            aq_data = aq_response.json()

            components = aq_data["list"][0]["components"]
            aqi = aq_data["list"][0]["main"]["aqi"]
            result = {
                "success": True,
                "city": geo_data[0]["name"],
                "aqi": aqi,
                "aqi_label": AQI_LABELS[aqi],
                "aqi_color": AQI_COLORS[aqi],
                "pm2_5": round(components["pm2_5"], 1),
                "pm10": round(components["pm10"], 1),
                "o3": round(components["o3"], 1),
                "no2": round(components["no2"], 1),
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache(f"air_quality_{city}", result)
    return result


@app.get("/api/hackernews")
async def get_hackernews():
    cached = get_from_cache("hackernews")
    if cached:
        return cached

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            ids_response = await client.get(
                "https://hacker-news.firebaseio.com/v0/topstories.json"
            )
            ids_response.raise_for_status()
            top_ids = ids_response.json()[:5]

            import asyncio

            async def fetch_story(story_id: int) -> dict:
                r = await client.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                )
                r.raise_for_status()
                return r.json()

            stories_raw = await asyncio.gather(*[fetch_story(i) for i in top_ids])
            stories = [
                {
                    "title": s.get("title", ""),
                    "url": s.get("url", f"https://news.ycombinator.com/item?id={s['id']}"),
                    "score": s.get("score", 0),
                    "by": s.get("by", ""),
                    "comments": s.get("descendants", 0),
                }
                for s in stories_raw
            ]
            result = {"success": True, "stories": stories}
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache("hackernews", result)
    return result


@app.get("/api/onthisday")
async def get_on_this_day():
    cached = get_from_cache("onthisday")
    if cached:
        return cached

    today = datetime.now()
    url = f"https://en.wikipedia.org/api/rest_v1/feed/onthisday/events/{today.month}/{today.day}"

    async with httpx.AsyncClient(timeout=5) as client:
        try:
            r = await client.get(url, headers={"Accept": "application/json"})
            r.raise_for_status()
            data = r.json()
            events = [
                {
                    "year": e["year"],
                    "text": e["text"],
                    "link": e.get("pages", [{}])[0].get("content_urls", {}).get("desktop", {}).get("page", ""),
                }
                for e in data.get("events", [])[:5]
            ]
            result = {
                "success": True,
                "date": today.strftime("%B") + " " + str(today.day),
                "events": events,
            }
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache("onthisday", result)
    return result


@app.get("/api/github-trending")
async def get_github_trending():
    cached = get_from_cache("github_trending")
    if cached:
        return cached

    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    url = (
        "https://api.github.com/search/repositories"
        f"?q=created:>{week_ago}&sort=stars&order=desc&per_page=5"
    )

    async with httpx.AsyncClient(timeout=5, headers={"Accept": "application/vnd.github.v3+json"}) as client:
        try:
            r = await client.get(url)
            r.raise_for_status()
            repos = [
                {
                    "name": repo["full_name"],
                    "description": repo.get("description") or "",
                    "stars": repo["stargazers_count"],
                    "language": repo.get("language") or "—",
                    "url": repo["html_url"],
                }
                for repo in r.json().get("items", [])
            ]
            result = {"success": True, "repos": repos}
        except Exception as e:
            result = {"success": False, "error": str(e)}

    set_cache("github_trending", result)
    return result


def run():
    import uvicorn
    uvicorn.run("api_dashboard.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    run()
