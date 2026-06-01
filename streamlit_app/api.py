import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("STREAMLIT_API_BASE_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "")

# A shared session that retries through free-tier cold starts. Render spins the
# service down when idle; the first request after that can fail or take ~50s.
# backoff_factor=2 → waits 0,2,4,8,16,32s between retries (~60s total budget),
# which covers the cold start so the user sees data instead of an error.
_retry = Retry(
    total=6,
    connect=6,
    read=6,
    backoff_factor=2,
    status_forcelist=[502, 503, 504],
    allowed_methods=["GET", "POST"],
)
_session = requests.Session()
_adapter = HTTPAdapter(max_retries=_retry)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


def _headers():
    h = {"Content-Type": "application/json"}
    if API_KEY:
        h["X-API-Key"] = API_KEY
    return h


def _url(path):
    return f"{API_BASE}{path}"


def warm_up():
    """Ping the backend to wake it from sleep. Returns True if reachable."""
    try:
        r = _session.get(_url("/health"), timeout=60)
        return r.ok
    except requests.RequestException:
        return False


def get(path, params=None):
    r = _session.get(_url(path), headers=_headers(), params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def post(path, data=None):
    r = _session.post(_url(path), headers=_headers(), json=data, timeout=90)
    r.raise_for_status()
    return r.json()
