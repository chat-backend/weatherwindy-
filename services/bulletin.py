# services/bulletin.py
import random
from typing import Dict, Any, List, Tuple
from services.weather_sources import get_weather
from services.current import build_current_block
from services.overview import build_overview_block
from services.summary import build_summary
from services.insights import generate_all_insights
from services.alerts import generate_all_alerts

def _code_to_text(code):
    mapping = {
        0: "Quang mây", 1: "Ít mây", 2: "Mây vừa", 3: "Nhiều mây",
        45: "Sương mù", 48: "Sương mù (sương đóng băng)",
        51: "Mưa phùn nhẹ", 53: "Mưa phùn vừa", 55: "Mưa phùn nặng",
        61: "Mưa nhẹ", 63: "Mưa vừa", 65: "Mưa to",
        80: "Mưa rào nhẹ", 81: "Mưa rào vừa", 82: "Mưa rào nặng",
        95: "Dông", 96: "Dông (mưa đá nhẹ)", 99: "Dông (mưa đá mạnh)",
    }
    return mapping.get(code, "—")

def choose_weather_icon(status: str) -> str:
    if not status:
        return "default.ico"
    s = (status or "").lower()
    if "nắng" in s or "quang" in s or "sun" in s:
        return "sun.ico"
    elif "mây" in s or "cloud" in s:
        return "cloud.ico"
    elif "mưa" in s or "rain" in s:
        return "rain.ico"
    elif "tuyết" in s or "snow" in s:
        return "snow.ico"
    elif "dông" in s or "storm" in s:
        return "storm.ico"
    else:
        return random.choice(["sun.ico", "cloud.ico", "rain.ico"])

def categorize_alerts(all_alerts: List[str]) -> Dict[str, List[str]]:
    def has_any(s: str, keys: List[str]) -> bool:
        low = s.lower()
        return any(k in low for k in keys)

    categories: Dict[str, List[str]] = {
        "temp": [], "rain": [], "wind": [], "humidity": [],
        "pressure": [], "uv": [], "solar": [],
    }

    for a in all_alerts or []:
        if has_any(a, ["nhiệt độ", "sốc nhiệt", "hạ thân nhiệt", "nắng nóng", "nóng", "lạnh", "rét"]):
            categories["temp"].append(a)
        if has_any(a, ["mưa", "lũ", "ngập", "mưa rào", "mưa to", "mưa đá", "dông", "giông"]):
            categories["rain"].append(a)
        if has_any(a, ["gió", "bão", "giật", "gió mạnh", "gió giật", "cấp gió"]):
            categories["wind"].append(a)
        if has_any(a, ["độ ẩm", "nồm", "ẩm mốc", "khô hạn", "ẩm ướt"]):
            categories["humidity"].append(a)
        if has_any(a, ["áp suất", "áp thấp", "cao áp", "baro", "barometric"]):
            categories["pressure"].append(a)
        if has_any(a, ["uv", "cháy nắng", "tia uv", "tia cực tím"]):
            categories["uv"].append(a)
        if has_any(a, ["bức xạ", "solar", "w/m²", "radiation"]):
            categories["solar"].append(a)

    return categories

# ---------------- Mapping về unified ----------------
def map_to_unified(current: Dict[str, Any], hourly: Dict[str, Any], daily: Dict[str, Any]) -> Dict[str, Any]:
    """Chuyển dữ liệu từ get_weather sang unified key mà các block đang dùng."""
    unified: Dict[str, Any] = {}

    # Current
    unified["temperature_now"] = current.get("temperature")
    unified["apparent_temperature_now"] = current.get("apparent_temperature")
    unified["humidity_now"] = current.get("humidity")
    unified["pressure_now"] = current.get("pressure")
    unified["wind_speed_now"] = current.get("wind_speed")
    unified["gust_now"] = current.get("gust")
    unified["solar_radiation_now"] = current.get("solar_radiation")
    unified["uv_index_now"] = current.get("uv_index")
    unified["precipitation_now"] = current.get("precipitation")
    unified["precipitation_probability_now"] = current.get("precipitation_probability")
    unified["wind_direction_now"] = current.get("wind_direction")
    unified["cloudcover_now"] = current.get("cloudcover")
    unified["dewpoint_now"] = current.get("dewpoint")
    unified["visibility_now"] = current.get("visibility")  # Open-Meteo không có
    unified["status_code_now"] = current.get("status_code")

    # Hourly (avg)
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
    unified["dewpoint_hourly"] = hourly.get("avg_dewpoint")

    # Daily (day aggregates)
    unified["temperature_min"] = daily.get("temperature_min")
    unified["temperature_max"] = daily.get("temperature_max")
    unified["temperature_day"] = daily.get("avg_temperature")
    unified["precipitation_sum_day"] = daily.get("precipitation_sum")
    unified["precipitation_probability_day"] = daily.get("precipitation_probability")
    unified["humidity_day"] = daily.get("avg_humidity")
    unified["pressure_day"] = daily.get("avg_pressure")
    unified["solar_radiation_sum_day"] = daily.get("solar_radiation_sum")
    unified["uv_index_max_day"] = daily.get("uv_index_max")
    unified["cloudcover_mean"] = daily.get("cloudcover_mean")
    unified["dewpoint_2m_mean"] = daily.get("dewpoint_2m_mean")
    unified["sunrise"] = daily.get("sunrise")
    unified["sunset"] = daily.get("sunset")

    # Các trường không có từ API hiện tại -> để None
    unified["wind_speed_10m_max"] = None
    unified["wind_gusts_10m_max"] = None

    return unified

# ---------------- ASYNC VERSION ----------------
async def build_bulletin_unified(
    lat: float,
    lon: float,
    loc: Dict[str, Any] = None
) -> Dict[str, Any]:
    if loc is None:
        loc = {}

    # Lấy dữ liệu nguồn chuẩn
    om_data = await get_weather(lat, lon)
    current = om_data.get("current", {}) or {}
    hourly = om_data.get("hourly", {}) or {}
    daily = om_data.get("daily", {}) or {}

    # Map về unified cho các block
    unified = map_to_unified(current, hourly, daily)

    # Status text từ code hiện tại
    status_code = unified.get("status_code_now")
    status_text = _code_to_text(status_code)

    wind_unit = "m/s"

    # Tính cực đại ngày từ hourly series
    series = hourly.get("series", {}) or {}
    wspd_series = series.get("wind_speed_10m") or []
    gust_series = series.get("wind_gusts_10m") or []

    wind_speed_max = max([v for v in wspd_series if v is not None], default=None)
    wind_gusts_max = max([v for v in gust_series if v is not None], default=None)

    # ---------------- BLOCKS ----------------
    current_block, current_values = build_current_block(
        unified, status_text, wind_unit
    )

    overview_block, overview_values = build_overview_block(
        daily={
            "precipitation_sum": unified.get("precipitation_sum_day"),
            "avg_wind_speed_day": unified.get("wind_speed_hourly"),  # dùng hourly avg làm daily avg
            "avg_humidity": unified.get("humidity_day"),
            "avg_pressure": unified.get("pressure_day"),
            "solar_radiation_sum": unified.get("solar_radiation_sum_day"),
        },
        status_text=status_text,
        tmin=unified.get("temperature_min"),
        tmax=unified.get("temperature_max"),
        uv_max_day=unified.get("uv_index_max_day"),
        hourly={
            "temperature_hourly": unified.get("temperature_hourly"),
            "uv_index_hourly": unified.get("uv_index_hourly"),
        },
        sunrise=unified.get("sunrise"),
        sunset=unified.get("sunset"),
        wind_speed_max=wind_speed_max,
        wind_gusts_max=wind_gusts_max,
        cloudcover_mean=unified.get("cloudcover_mean"),
        dewpoint_mean=unified.get("dewpoint_2m_mean"),
    )

    # Gom nhận định và cảnh báo chung
    all_insights = generate_all_insights(unified) or []
    all_alerts = generate_all_alerts(unified) or []

    summary_obj = build_summary(
        current_block=current_block,
        overview_block=overview_block,
        current_values=current_values,
        overview_values=overview_values,
        insights=all_insights,
        alerts=all_alerts
    )
    summary_block = summary_obj.get("summary_block", "")

    # ---------------- ALERTS ----------------
    cats = categorize_alerts(all_alerts)

    severity_map = {
        "lũ quét": (3, "🔴 Rất nguy hiểm"),
        "sạt lở": (3, "🔴 Rất nguy hiểm"),
        "bão": (3, "🔴 Rất nguy hiểm"),
        "sốc nhiệt": (2, "🟠 Nguy hiểm vừa"),
        "cháy nắng": (2, "🟠 Nguy hiểm vừa"),
        "hạ thân nhiệt": (2, "🟠 Nguy hiểm vừa"),
        "sương mù": (1, "🟢 Nhẹ"),
    }
    def get_severity(alert: str) -> Tuple[int, str]:
        low = alert.lower()
        for kw, (score, label) in severity_map.items():
            if kw in low:
                return score, label
        return 0, "⚪ An toàn"

    alerts_with_labels = [(get_severity(a)[0], f"{get_severity(a)[1]} - {a}") for a in all_alerts]
    sorted_alerts = sorted(alerts_with_labels, key=lambda x: x[0], reverse=True)

    if sorted_alerts:
        top_alerts = [a for _, a in sorted_alerts[:2]]
        highlight_text = "🚨 Cảnh báo nổi bật:\n" + "\n".join(top_alerts)
        highest_score = sorted_alerts[0][0]
        highest_label = sorted_alerts[0][1].split(" - ")[0]
    else:
        highlight_text = "✅ Không có cảnh báo nổi bật."
        highest_score, highest_label = 0, "⚪ An toàn"

    if highest_score == 3:
        bulletin_icon, severity_emoji = "danger_red.ico", "🔴"
    elif highest_score == 2:
        bulletin_icon, severity_emoji = "warning_orange.ico", "🟠"
    elif highest_score == 1:
        bulletin_icon, severity_emoji = "info_green.ico", "🟢"
    else:
        bulletin_icon = choose_weather_icon(status_text)
        severity_emoji = "⚪"

    summary_line = f"📊 Đánh giá tổng quan: {highest_label}"

    # ---------------- RETURN ----------------
    text = (
        "# 📰 BẢN TIN THỜI TIẾT\n\n"
        "## ⏱️ TÌNH HÌNH HIỆN TẠI\n" + (current_block or "—") + "\n\n"
        "## 📅 TỔNG QUAN TRONG NGÀY\n" + (overview_block or "—") + "\n\n"
        "## 🎯 KẾT LUẬN BẢN TIN\n" + (summary_block or "—") + "\n\n"
        + severity_emoji + " " + highlight_text + "\n"
        + summary_line
    )

    return {
        "text": text,
        "icon": bulletin_icon,
        "current_block": current_block or "",
        "overview_block": overview_block or "",
        "summary_block": summary_block or "",
        "insights": all_insights,
        "alerts": all_alerts,
        "categorized_alerts": cats,
        "data": {
            "current": current,
            "hourly": hourly,
            "daily": daily,
            "unified": unified,
            "loc": loc
        }
    }