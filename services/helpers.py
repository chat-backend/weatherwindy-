# services/helpers.py
import time
import hashlib
import requests
import asyncio
from typing import Dict, Any, Optional

from configs import (
    OPEN_METEO_GEOCODE, OPEN_METEO_REVERSE,
    CACHE_TTL_SECONDS,
    REQUEST_TIMEOUT
)

from services.weather_sources import get_weather
from vietnam_provinces import PROVINCES
from vietnam_wards import WARDS

# --------------------------------------
# Cache đơn giản trong bộ nhớ
# --------------------------------------
CACHE: Dict[str, Dict[str, Any]] = {}

def cache_get(key: str) -> Optional[Dict[str, Any]]:
    item = CACHE.get(key)
    if not item or time.time() - item["ts"] > CACHE_TTL_SECONDS:
        CACHE.pop(key, None)
        return None
    return item["data"]

def cache_set(key: str, data: Dict[str, Any]) -> None:
    CACHE[key] = {"ts": time.time(), "data": data}

# --------------------------------------
# Helpers
# --------------------------------------
def normalize(s: str) -> str:
    return (s or "").strip().lower()

def hash_key(*parts: Any) -> str:
    return hashlib.md5(",".join(map(str, parts)).encode("utf-8")).hexdigest()

def request_json(url: str, params: Dict[str, Any], timeout: int = 12) -> Dict[str, Any]:
    r = requests.get(url, params=params, headers={"Accept": "application/json"}, timeout=timeout)
    r.raise_for_status()
    return r.json()

# --------------------------------------
# Gom tất cả địa danh
# --------------------------------------
def get_all_locations() -> Dict[str, Any]:
    all_locations = {}
    all_locations.update(PROVINCES)
    all_locations.update(WARDS)
    return all_locations

def log_locations_summary(log):
    all_locations = get_all_locations()
    log.info(f"📍 Tổng số địa danh sau khi gộp: {len(all_locations)}")
    log.info(f"📍 PROVINCES: {len(PROVINCES)}")
    log.info(f"📍 WARDS: {len(WARDS)}")
    sample_names = list(all_locations.keys())[:10]
    log.debug(f"Ví dụ 10 địa danh đầu tiên: {sample_names}")

# --------------------------------------
# Geocode địa danh
# --------------------------------------
def geocode_region(region: str) -> Dict[str, Any]:
    rgn = (region or "").strip()

    if "," in rgn:
        try:
            la, lo = [float(x) for x in rgn.split(",")]
            return {
                "name": "Tọa độ",
                "latitude": la,
                "longitude": lo,
                "country": "Việt Nam",
                "admin1": ""
            }
        except Exception:
            pass

    key = normalize(region)
    for name, info in get_all_locations().items():
        if key == normalize(name) or key in [normalize(a) for a in info.get("aliases", [])]:
            return {
                "name": name,
                "latitude": info["lat"],
                "longitude": info["lon"],
                "country": "Việt Nam",
                "admin1": info.get("admin1") or name
            }

    j = request_json(OPEN_METEO_GEOCODE, {"name": region, "language": "vi", "count": 1})
    res = j.get("results") or []
    if not res:
        raise ValueError("Không tìm thấy địa danh")
    return res[0]

# -------------------------------
# Forecast hợp nhất (đồng bộ với weather_sources)
# -------------------------------
async def fetch_forecast_combined(lat: float, lon: float) -> dict:
    out: Dict[str, Any] = {"openmeteo": {}, "unified": {}}

    try:
        out["openmeteo"] = await get_weather(lat, lon)
    except Exception as e:
        out["openmeteo"] = {"error": str(e)}

    current = out.get("openmeteo", {}).get("current", {}) or {}
    hourly = out.get("openmeteo", {}).get("hourly", {}) or {}
    daily = out.get("openmeteo", {}).get("daily", {}) or {}

    unified: Dict[str, Any] = {}

    # --- CURRENT ---
    unified["temperature_now"] = current.get("temperature")
    unified["apparent_temperature_now"] = current.get("apparent_temperature")
    unified["humidity_now"] = current.get("humidity")
    unified["pressure_now"] = current.get("pressure")
    unified["wind_speed_now"] = current.get("wind_speed")
    unified["gust_now"] = current.get("gust")
    unified["wind_direction_now"] = current.get("wind_direction")
    unified["solar_radiation_now"] = current.get("solar_radiation")
    unified["uv_index_now"] = current.get("uv_index")
    unified["precipitation_now"] = current.get("precipitation")
    unified["precipitation_probability_now"] = current.get("precipitation_probability")
    unified["cloudcover_now"] = current.get("cloudcover")
    unified["dewpoint_now"] = current.get("dewpoint")
    unified["visibility_now"] = current.get("visibility_now")
    unified["status_code_now"] = current.get("status_code")

    # ✅ Thêm trường intensity_ratio_now
    try:
        rain_now = current.get("precipitation")
        avg_rain_hour = hourly.get("avg_precipitation")
        if rain_now is not None and avg_rain_hour not in (None, 0):
            unified["intensity_ratio_now"] = round(float(rain_now) / float(avg_rain_hour), 1)
        else:
            unified["intensity_ratio_now"] = None
    except Exception:
        unified["intensity_ratio_now"] = None

    # --- HOURLY ---
    unified["temperature_hourly"] = hourly.get("avg_temperature")
    unified["apparent_temperature_hourly"] = hourly.get("avg_apparent_temperature")
    unified["humidity_hourly"] = hourly.get("avg_humidity")
    unified["pressure_hourly"] = hourly.get("avg_pressure")
    unified["wind_speed_hourly"] = hourly.get("avg_wind_speed")
    unified["gust_hourly"] = hourly.get("avg_gust")
    unified["precipitation_hourly"] = hourly.get("avg_precipitation")
    unified["precipitation_probability_hourly"] = hourly.get("avg_precipitation_probability")
    unified["uv_index_hourly"] = hourly.get("avg_uv_index")
    unified["solar_radiation_hourly"] = hourly.get("avg_solar_radiation")
    unified["cloudcover_hourly"] = hourly.get("avg_cloudcover")
    unified["visibility_hourly"] = hourly.get("avg_visibility")
    unified["dewpoint_hourly"] = hourly.get("avg_dewpoint")

    # ✅ Thêm trường intensity_ratio_hourly (so sánh trung bình giờ với trung bình ngày)
    try:
        avg_rain_hour = hourly.get("avg_precipitation")
        avg_rain_day = unified.get("precipitation_day")  # đã tính ở block DAILY
        if avg_rain_hour is not None and avg_rain_day not in (None, 0):
            unified["intensity_ratio_hourly"] = round(float(avg_rain_hour) / float(avg_rain_day), 1)
        else:
            unified["intensity_ratio_hourly"] = None
    except Exception:
        unified["intensity_ratio_hourly"] = None

    # --- DAILY ---
    daily_data = out["openmeteo"].get("daily", {}) or {}
    hourly_data = out["openmeteo"].get("hourly", {}) or {}

    # Tổng lượng mưa ngày (đã chuẩn hóa fallback trong weather_sources)
    precip_sum_day = daily_data.get("precipitation_sum")

    # Trung bình ngày: tính từ tổng lượng mưa / số giờ thực tế trong ngày
    precip_day = None
    try:
        if precip_sum_day is not None:
            today_str = datetime.date.today().isoformat()
            # Đếm số giờ trong ngày hiện tại
            hours_today = [
                t for t in hourly_data.get("series", {}).get("time", [])
                if t.startswith(today_str)
            ]
            hours_count = len(hours_today)
            if hours_count > 0:
                precip_day = round(float(precip_sum_day) / hours_count, 1)
    except Exception:
        precip_day = None

    unified["temperature_2m_min_day"] = daily_data.get("temperature_min")
    unified["temperature_2m_max_day"] = daily_data.get("temperature_max")
    unified["temperature_day"] = daily_data.get("avg_temperature")
    unified["precipitation_sum_day"] = precip_sum_day
    unified["precipitation_day"] = precip_day   # ✅ trung bình ngày theo số giờ thực tế
    unified["precipitation_probability_day"] = daily_data.get("precipitation_probability_day")
    unified["humidity_day"] = daily_data.get("avg_humidity")
    unified["pressure_day"] = daily_data.get("avg_pressure")
    unified["solar_radiation_sum_day"] = daily_data.get("solar_radiation_sum")
    unified["uv_index_max_day"] = daily_data.get("uv_index_max")
    unified["cloudcover_mean"] = daily_data.get("cloudcover_mean")
    unified["dewpoint_2m_mean"] = daily_data.get("dewpoint_2m_mean")
    unified["visibility_day"] = daily_data.get("visibility_day")
    unified["sunrise"] = daily_data.get("sunrise")
    unified["sunset"] = daily_data.get("sunset")

    # ✅ Thêm trường intensity_ratio_day (so sánh trung bình ngày với tổng ngày)
    try:
        if precip_day is not None and precip_sum_day not in (None, 0):
            unified["intensity_ratio_day"] = round(float(precip_day) / float(precip_sum_day), 3)
        else:
            unified["intensity_ratio_day"] = None
    except Exception:
        unified["intensity_ratio_day"] = None

    out["unified"] = unified
    return out

# --------------------------------------
# Reverse Geocode
# --------------------------------------
def reverse_geocode(lat: float, lon: float) -> Dict[str, Any]:
    for name, info in get_all_locations().items():
        if abs(info["lat"] - lat) < 0.001 and abs(info["lon"] - lon) < 0.001:
            return {
                "name": name,
                "latitude": info["lat"],
                "longitude": info["lon"],
                "country": "Việt Nam",
                "admin1": info.get("admin1") or name
            }

    try:
        j = request_json(
            OPEN_METEO_REVERSE,
            {"latitude": lat, "longitude": lon, "language": "vi", "count": 1}
        )
        res = j.get("results") or []
        if not res:
            raise ValueError("Không tìm thấy địa danh cho tọa độ đã cho")
        return res[0]
    except Exception as e:
        return {"error": str(e)}