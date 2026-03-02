# Backwards-compatibility shim — the app now lives in api_dashboard/main.py
from api_dashboard.main import app  # noqa: F401
