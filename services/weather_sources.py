# services/weather_sources.py
import httpx
import datetime
from typing import Dict, Any
from zoneinfo import ZoneInfo

OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"

def _first(v):
    if isinstance(v, list) and v:
        return v[0]
    return v

def _round1(val):
    try:
        return None if val is None else round(float(val), 1)
    except Exception:
        return None

async def fetch_openmeteo(lat: float, lon: float) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(
            OPEN_METEO_FORECAST,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "hourly": (
                    "temperature_2m,apparent_temperature,precipitation,"
                    "precipitation_probability,wind_speed_10m,wind_gusts_10m,"
                    "winddirection_10m,relative_humidity_2m,pressure_msl,"
                    "shortwave_radiation,uv_index,cloudcover,dewpoint_2m,visibility"
                ),
                "daily": (
                    "temperature_2m_max,temperature_2m_min,temperature_2m_mean,"
                    "precipitation_sum,precipitation_probability_mean,"
                    "relative_humidity_2m_mean,pressure_msl_mean,"
                    "shortwave_radiation_sum,uv_index_max,"
                    "sunrise,sunset,cloudcover_mean,dewpoint_2m_mean"
                )
            }
        )
        resp.raise_for_status()
        return resp.json()

async def get_weather(lat: float, lon: float) -> Dict[str, Any]:
    om = await fetch_openmeteo(lat, lon)

    # Align VN local time to UTC hourly index
    now_local = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).replace(minute=0, second=0, microsecond=0)
    now = now_local.astimezone(datetime.timezone.utc)
    times = om.get("hourly", {}).get("time", [])
    idx = None
    if times:
        try:
            idx = times.index(now.isoformat(timespec="minutes"))
        except ValueError:
            now_naive = now.replace(tzinfo=None)
            idx = min(range(len(times)), key=lambda i: abs(datetime.datetime.fromisoformat(times[i]) - now_naive))

    cw = om.get("current_weather", {}) or {}
    hourly = om.get("hourly", {}) or {}
    daily = om.get("daily", {}) or {}

    # Current (instant)
    om_current = {
        "temperature": _round1(cw.get("temperature")),
        "apparent_temperature": _round1(hourly.get("apparent_temperature", [None])[idx]) if idx is not None else None,
        "wind_speed": _round1(cw.get("windspeed")),
        "gust": _round1(cw.get("windgusts")) if cw.get("windgusts") is not None else _round1(cw.get("windspeed")),
        "wind_direction": _round1(cw.get("winddirection")) if cw.get("winddirection") is not None else None,
        "precipitation": _round1(hourly.get("precipitation", [None])[idx]) if idx is not None else None,
        "precipitation_probability": _round1(hourly.get("precipitation_probability", [None])[idx]) if idx is not None else None,
        "humidity": _round1(hourly.get("relative_humidity_2m", [None])[idx]) if idx is not None else None,
        "pressure": _round1(hourly.get("pressure_msl", [None])[idx]) if idx is not None else None,
        "solar_radiation": _round1(hourly.get("shortwave_radiation", [None])[idx]) if idx is not None else None,
        "uv_index": _round1(hourly.get("uv_index", [None])[idx]) if idx is not None else None,
        "cloudcover": _round1(hourly.get("cloudcover", [None])[idx]) if idx is not None else None,
        "dewpoint": _round1(hourly.get("dewpoint_2m", [None])[idx]) if idx is not None else None,
        "visibility": _round1(hourly.get("visibility", [None])[idx]) if idx is not None else None,
        "status_code": cw.get("weathercode"),
    }

    # Hourly (24h averages)
    def _safe_avg(values: list) -> Any:
        try:
            vals = [float(x) for x in values if x is not None]
            if not vals:
                return None
            return round(sum(vals) / len(vals), 1)
        except Exception:
            return None

    om_hourly = {
        "avg_temperature": _safe_avg(hourly.get("temperature_2m", [])),
        "avg_apparent_temperature": _safe_avg(hourly.get("apparent_temperature", [])),
        "avg_wind_speed": _safe_avg(hourly.get("wind_speed_10m", [])),
        "avg_gust": _safe_avg(hourly.get("wind_gusts_10m", [])),
        "avg_precipitation": _safe_avg(hourly.get("precipitation", [])),
        "avg_precipitation_probability": _safe_avg(hourly.get("precipitation_probability", [])),
        "avg_humidity": _safe_avg(hourly.get("relative_humidity_2m", [])),
        "avg_pressure": _safe_avg(hourly.get("pressure_msl", [])),
        "avg_solar_radiation": _safe_avg(hourly.get("shortwave_radiation", [])),
        "avg_uv_index": _safe_avg(hourly.get("uv_index", [])),
        "avg_cloudcover": _safe_avg(hourly.get("cloudcover", [])),
        "avg_dewpoint": _safe_avg(hourly.get("dewpoint_2m", [])),
        "avg_visibility": _safe_avg(hourly.get("visibility", [])),
        "series": {
            "time": hourly.get("time", []),
            "temperature_2m": hourly.get("temperature_2m", []),
            "apparent_temperature": hourly.get("apparent_temperature", []),
            "wind_speed_10m": hourly.get("wind_speed_10m", []),
            "wind_gusts_10m": hourly.get("wind_gusts_10m", []),
            "winddirection_10m": hourly.get("winddirection_10m", []),
            "precipitation": hourly.get("precipitation", []),
            "precipitation_probability": hourly.get("precipitation_probability", []),
            "relative_humidity_2m": hourly.get("relative_humidity_2m", []),
            "pressure_msl": hourly.get("pressure_msl", []),
            "shortwave_radiation": hourly.get("shortwave_radiation", []),
            "uv_index": hourly.get("uv_index", []),
            "cloudcover": hourly.get("cloudcover", []),
            "dewpoint_2m": hourly.get("dewpoint_2m", []),
            "visibility": hourly.get("visibility", []),
        }
    }

    # Daily
    # Nếu daily có precipitation_sum hợp lệ thì dùng,
    # nếu không (None) thì fallback cộng dồn từ hourly series
    daily_precip = _first(daily.get("precipitation_sum"))
    if daily_precip is None:  # ✅ chỉ fallback khi None, không khi bằng 0
        try:
            daily_precip = sum(
                float(v) for v in hourly.get("precipitation", []) if v is not None
            )
        except Exception:
            daily_precip = None

    om_daily = {
        "temperature_min": _round1(_first(daily.get("temperature_2m_min"))),
        "temperature_max": _round1(_first(daily.get("temperature_2m_max"))),
        "avg_temperature": _round1(_first(daily.get("temperature_2m_mean"))) if daily.get("temperature_2m_mean") else None,
        "precipitation_sum": _round1(daily_precip),
        "precipitation_probability": _round1(_first(daily.get("precipitation_probability_mean"))) if daily.get("precipitation_probability_mean") else None,
        "precipitation_probability_day": _round1(_first(daily.get("precipitation_probability_mean"))) if daily.get("precipitation_probability_mean") else None,  # ✅ alias thêm vào
        "avg_humidity": _round1(_first(daily.get("relative_humidity_2m_mean"))) if daily.get("relative_humidity_2m_mean") else None,
        "avg_pressure": _round1(_first(daily.get("pressure_msl_mean"))) if daily.get("pressure_msl_mean") else None,
        "solar_radiation_sum": _round1(_first(daily.get("shortwave_radiation_sum"))) if daily.get("shortwave_radiation_sum") else None,
        "uv_index_max": _round1(_first(daily.get("uv_index_max"))),
        "sunrise": _first(daily.get("sunrise")),
        "sunset": _first(daily.get("sunset")),
        "cloudcover_mean": _round1(_first(daily.get("cloudcover_mean"))) if daily.get("cloudcover_mean") else None,
        "dewpoint_2m_mean": _round1(_first(daily.get("dewpoint_2m_mean"))) if daily.get("dewpoint_2m_mean") else None,
        "visibility_day": _round1(_first(daily.get("visibility"))) if daily.get("visibility") else None,

        "series": {
            "time": daily.get("time", []),
            "temperature_2m_min": daily.get("temperature_2m_min", []),
            "temperature_2m_max": daily.get("temperature_2m_max", []),
            "temperature_2m_mean": daily.get("temperature_2m_mean", []),
            "precipitation_sum": daily.get("precipitation_sum", []),
            "precipitation_probability_mean": daily.get("precipitation_probability_mean", []),
            "relative_humidity_2m_mean": daily.get("relative_humidity_2m_mean", []),
            "pressure_msl_mean": daily.get("pressure_msl_mean", []),
            "shortwave_radiation_sum": daily.get("shortwave_radiation_sum", []),
            "uv_index_max": daily.get("uv_index_max", []),
            "sunrise": daily.get("sunrise", []),
            "sunset": daily.get("sunset", []),
            "cloudcover_mean": daily.get("cloudcover_mean", []),
            "dewpoint_2m_mean": daily.get("dewpoint_2m_mean", []),
            "visibility": daily.get("visibility", []),
        }
    }

    return {"current": om_current, "hourly": om_hourly, "daily": om_daily}