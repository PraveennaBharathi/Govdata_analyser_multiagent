"""
Real-time Singapore city data — no API key required.
Sources: NEA via api-open.data.gov.sg
"""
import logging
import time
from typing import Dict, Any
import urllib.request
import json

logger = logging.getLogger(__name__)

_CACHE: Dict[str, Any] = {}
_CACHE_TTL = 600  # 10 minutes for real-time data

PSI_URL     = "https://api-open.data.gov.sg/v2/real-time/api/psi"
WEATHER_URL = "https://api-open.data.gov.sg/v2/real-time/api/two-hr-forecast"

HEADERS = {"User-Agent": "GovDataAnalytics/1.0"}


def _fetch(url: str) -> Dict:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())


def _psi_category(val: float) -> str:
    if val <= 50:   return "Good"
    if val <= 100:  return "Moderate"
    if val <= 200:  return "Unhealthy"
    if val <= 300:  return "Very Unhealthy"
    return "Hazardous"


def _psi_color(val: float) -> str:
    if val <= 50:   return "green"
    if val <= 100:  return "yellow"
    if val <= 200:  return "orange"
    if val <= 300:  return "red"
    return "purple"


def get_live_city_data() -> Dict[str, Any]:
    now = time.time()
    if "live_city" in _CACHE and now - _CACHE["live_city"]["_ts"] < _CACHE_TTL:
        return _CACHE["live_city"]["data"]

    result: Dict[str, Any] = {"status": "success"}

    # ── PSI ──────────────────────────────────────────────────────────────────
    try:
        psi_raw = _fetch(PSI_URL)
        item = psi_raw["data"]["items"][0]
        readings = item["readings"]
        timestamp = item["timestamp"]

        psi_by_region = readings.get("psi_twenty_four_hourly", {})
        pm25_by_region = readings.get("pm25_twenty_four_hourly", {})
        pm10_by_region = readings.get("pm10_twenty_four_hourly", {})

        overall_psi = max(psi_by_region.values()) if psi_by_region else 0

        result["psi"] = {
            "timestamp": timestamp,
            "overall": overall_psi,
            "category": _psi_category(overall_psi),
            "color": _psi_color(overall_psi),
            "by_region": {
                region: {
                    "psi": psi_by_region.get(region, 0),
                    "pm25": pm25_by_region.get(region, 0),
                    "pm10": pm10_by_region.get(region, 0),
                    "category": _psi_category(psi_by_region.get(region, 0)),
                }
                for region in ["north", "south", "east", "west", "central"]
            },
        }
    except Exception as e:
        logger.warning(f"PSI fetch failed: {e}")
        result["psi"] = None

    # ── Weather ───────────────────────────────────────────────────────────────
    try:
        wx_raw = _fetch(WEATHER_URL)
        wx_item = wx_raw["data"]["items"][0]
        forecasts = wx_item.get("forecasts", [])
        valid = wx_item.get("valid_period", {})

        # Summarise unique forecasts
        from collections import Counter
        counts = Counter(f["forecast"] for f in forecasts)
        most_common = counts.most_common(3)

        result["weather"] = {
            "timestamp": wx_item.get("timestamp"),
            "valid_start": valid.get("start"),
            "valid_end": valid.get("end"),
            "forecasts": forecasts,
            "summary": most_common[0][0] if most_common else "Unknown",
            "breakdown": [{"forecast": fc, "count": cnt} for fc, cnt in most_common],
        }
    except Exception as e:
        logger.warning(f"Weather fetch failed: {e}")
        result["weather"] = None

    _CACHE["live_city"] = {"_ts": now, "data": result}
    return result
