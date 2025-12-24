# services/overview.py
import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Tuple, Optional

from services.temperature import (
    compute_avg_temp, compute_diurnal_range, compute_hourly_anomaly, classify_temp_level
)
from services.rain import classify_rain_level, interpret_rain_probability
from services.wind import classify_wind_beaufort, classify_wind_level
from services.cloud_dew import build_cloud_dew_summary
from services.humidity import classify_humidity, adjust_feels_by_humidity
from services.pressure import classify_pressure
from services.solar_uv import (
    classify_solar,
    classify_uv,
    _is_night,
    _format_solar_sum,
    _format_uv_avg,
    _format_uv_max,
)

def _to_float(val: Any) -> Optional[float]:
    try:
        if val is None: return None
        return float(val)
    except Exception:
        return None

def _round1(val: Optional[float]) -> Optional[float]:
    return None if val is None else round(val, 1)

def fmt(val: Any, unit: str = "") -> str:
    if val is None: return "—"
    try:
        if isinstance(val, (int, float)):
            return f"{round(float(val), 1)}{unit}"
    except Exception:
        pass
    return f"{val}{unit}"

# -------------------------------
# Khối tổng quan trong ngày
# -------------------------------
def build_overview_block(
    daily: Dict[str, Any],
    status_text: str,
    tmin: Any,
    tmax: Any,
    uv_max_day: Any,
    hourly: Dict[str, Any],
    sunrise: Any = None,
    sunset: Any = None,
    wind_speed_max: Any = None,
    wind_gusts_max: Any = None,
    cloudcover_mean: Any = None,
    dewpoint_mean: Any = None,
    region: str = "north"
) -> Tuple[str, Dict[str, Any], List[str]]:
    # Nhiệt độ
    avg_temp_day = compute_avg_temp(daily.get("temperature_day"), tmin, tmax)
    diurnal_range = compute_diurnal_range(tmin, tmax)
    hourly_anomaly = compute_hourly_anomaly(avg_temp_day, hourly.get("temperature_hourly"))
    temp_level = classify_temp_level(avg_temp_day, region=region)

    # Mưa ngày
    rain_sum = _to_float(daily.get("precipitation_sum"))
    today_precips = None
    if (rain_sum is None or rain_sum == 0) and hourly.get("series", {}).get("precipitation"):
        try:
            times = hourly.get("series", {}).get("time", [])
            precips = hourly.get("series", {}).get("precipitation", [])
            today_str = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
            today_precips = [
                _to_float(v) or 0.0
                for i, v in enumerate(precips)
                if i < len(times) and isinstance(times[i], str) and times[i].startswith(today_str)
            ]
            rain_sum = sum(today_precips) if today_precips else None
        except Exception:
            rain_sum = None

    rain_now = _to_float(hourly.get("precipitation_now"))
    if (rain_sum is None or rain_sum == 0) and rain_now and rain_now > 0:
        rain_sum = rain_now

    rain_sum_val = _round1(rain_sum)
    rain_level_text = classify_rain_level(rain_sum)

    hours_count = len(today_precips) if isinstance(today_precips, list) else 0
    if hours_count == 0:
        times = hourly.get("series", {}).get("time", [])
        today_str = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
        def day_of(t): return t[:10] if isinstance(t, str) and len(t) >= 10 else None
        hours_count = sum(1 for t in times if day_of(t) == today_str)

    avg_precipitation_day = None
    if rain_sum is not None and hours_count > 0:
        avg_precipitation_day = _round1(rain_sum / hours_count)
    elif rain_sum is not None:
        avg_precipitation_day = _round1(rain_sum / 24.0)

    # Xác suất mưa
    precip_prob_day = daily.get("precipitation_probability_day") or daily.get("precipitation_probability")
    if precip_prob_day is None and hourly.get("series", {}).get("precipitation_probability"):
        try:
            times = hourly.get("series", {}).get("time", [])
            probs = hourly.get("series", {}).get("precipitation_probability", [])
            today_str = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).date().isoformat()
            today_probs = [
                _to_float(v) or 0.0
                for i, v in enumerate(probs)
                if i < len(times) and isinstance(times[i], str) and times[i].startswith(today_str)
            ]
            if today_probs:
                precip_prob_day = sum(today_probs) / len(today_probs)
        except Exception:
            precip_prob_day = None

    # Gió
    avg_wspd = daily.get("avg_wind_speed_day")
    wind_level = classify_wind_beaufort(avg_wspd)
    wind_level_desc = classify_wind_level(avg_wspd, region=region)

    # Mây, sương
    cloud_dew_summary = build_cloud_dew_summary(cloudcover_mean, dewpoint_mean)
    cloud_values = cloud_dew_summary["values"]
    cloud_lines = cloud_dew_summary["lines"]

    # Độ ẩm
    humidity_day = daily.get("avg_humidity")
    humidity_level = classify_humidity(humidity_day)
    adjusted_feels_humidity = adjust_feels_by_humidity(
        avg_temp_day, tmax, humidity_day, region=region
    )

    # Áp suất
    pressure_day = daily.get("avg_pressure")
    pressure_level = classify_pressure(pressure_day, region=region)

    # Bức xạ & UV
    now_local = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    is_night = _is_night(now_local)

    avg_solar_day = daily.get("avg_solar") or daily.get("solar_radiation_avg")
    solar_sum_day = daily.get("solar_radiation_sum")
    avg_uv_day    = daily.get("uv_index_avg")
    uv_max_val    = uv_max_day or daily.get("uv_index_max")

    solar_level  = None
    uv_level_avg = None
    uv_level_max = None

    # Hiển thị
    lines: List[str] = []
    lines.append(f"🌤️ Dự báo: {status_text or '—'}")

    # 🕒 Thời gian quan trắc
    weekday_map = {
        0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư",
        3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật"
    }
    weekday_vi = weekday_map[now_local.weekday()]
    timestamp = now_local.strftime(f"%H:%M • {weekday_vi}, %d/%m/%Y")
    lines.append(f"🕒 Thời gian quan trắc: {timestamp}")
    lines.append(f"📄 Nguồn dữ liệu: Open_MeteoAPI")
    lines.append("")
 
    if tmin is not None and tmax is not None:
        lines.append(f"🌡️ Dao động ngày: {fmt(_round1(_to_float(tmin)), '°C')} / {fmt(_round1(_to_float(tmax)), '°C')}")
    if avg_temp_day is not None:
        lines.append(f"🌡️ Nhiệt độ trung bình ngày: {fmt(_round1(_to_float(avg_temp_day)), '°C')}")
    if diurnal_range is not None:
        lines.append(f"📈 Biên độ nhiệt ngày: {fmt(_round1(_to_float(diurnal_range)), '°C')}")
    if hourly_anomaly is not None:
        lines.append(f"⏱️ Lệch theo giờ: {fmt(_round1(_to_float(hourly_anomaly)), '×')} (so với trung bình giờ)")
    if temp_level:
        lines.append(f"🏷️ Mức độ nhiệt độ: {temp_level}")

    if avg_precipitation_day is not None:
        lines.append(f"🌦️ Lượng mưa trung bình ngày: {fmt(avg_precipitation_day, ' mm/h')}")
    if precip_prob_day is not None:
        prob_val = int(round(_to_float(precip_prob_day)))
        prob_text = interpret_rain_probability(precip_prob_day)
        lines.append(
            f"📊 Xác suất mưa trung bình ngày: {fmt(prob_val, '%')} "
            f"({prob_text if prob_text else '—'})")
    if rain_sum_val is not None:
        lines.append(f"🌧️ Tổng lượng mưa ngày: {fmt(rain_sum_val, ' mm')}")
    if rain_level_text:
        lines.append(f"🏷️ Mức độ mưa: {rain_level_text}")

    if avg_wspd is not None:
        lines.append(f"💨 Gió trung bình ngày: {fmt(_round1(_to_float(avg_wspd)), ' m/s')}")
    if wind_speed_max is not None:
        lines.append(f"💨 Gió cực đại ngày: {fmt(_round1(_to_float(wind_speed_max)), ' m/s')}")
    if wind_gusts_max is not None:
        lines.append(f"💨 Gió giật cực đại ngày: {fmt(_round1(_to_float(wind_gusts_max)), ' m/s')}")
    if wind_level is not None:
        lines.append(f"🌀 Cấp gió Beaufort trung bình: {wind_level}")
    if wind_level_desc:
        lines.append(f"🍃 Mức độ gió: {wind_level_desc}")

    if cloud_values["cloudcover"] is not None:
        lines.append(f"☁️ Độ che phủ mây trung bình: {cloud_values['cloudcover']}% ({cloud_values['cloudcover_level'] if cloud_values['cloudcover_level'] else '—'})")
    if cloud_values["dewpoint"] is not None:
        lines.append(f"🌫️ Điểm sương trung bình: {cloud_values['dewpoint']}°C ({cloud_values['dewpoint_level'] if cloud_values['dewpoint_level'] else '—'})")
   
    if humidity_day is not None:
        lines.append(f"💧 Độ ẩm trung bình ngày: {fmt(_round1(_to_float(humidity_day)), '%')} ({humidity_level if humidity_level else '—'})")
    if adjusted_feels_humidity is not None:
        lines.append(f"🤔 Cảm giác thực tế (điều chỉnh theo độ ẩm): {fmt(_round1(_to_float(adjusted_feels_humidity)), '°C')}")

    if pressure_day is not None:
        lines.append(f"⚖️ Áp suất trung bình ngày: {fmt(_round1(_to_float(pressure_day)), ' hPa')} ({pressure_level if pressure_level else '—'})")

    # Bức xạ & UV
    if is_night:
        lines.append("🔆 Năng lượng bức xạ tích lũy trong ngày: 0 Wh/m² (🌙 Ban đêm)")
        lines.append("☀️ UV tối đa: 0 (🌙 Ban đêm, UV = 0)")
    else:
        avg_solar_val = _to_float(avg_solar_day) if avg_solar_day is not None else 0
        solar_level = classify_solar(avg_solar_val, region=region, now=now_local)

        lines.append(
            f"🔆 Năng lượng bức xạ tích lũy trong ngày: "
            f"{_format_solar_sum(solar_sum_day) if solar_sum_day is not None else '0 Wh/m²'}"
        )

        if avg_uv_day is not None:
            avg_uv_val = _to_float(avg_uv_day)
            uv_level_avg = classify_uv(avg_uv_val)
            lines.append(f"☀️ UV trung bình ngày: {fmt(avg_uv_val)} ({uv_level_avg or '—'})")

        uv_max_val_checked = _to_float(uv_max_val) if uv_max_val is not None else 0
        uv_level_max = classify_uv(uv_max_val_checked)
        lines.append(f"☀️ UV tối đa trong ngày: {fmt(uv_max_val_checked)} ({uv_level_max or '—'})")

    if sunrise:
        try:
            sunrise_dt = datetime.datetime.fromisoformat(str(sunrise))
            # API trả về UTC → gán tzinfo=UTC rồi chuyển sang ICT
            if sunrise_dt.tzinfo is None:
                sunrise_dt = sunrise_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
            else:
                sunrise_dt = sunrise_dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
            lines.append(f"🌅 Mặt trời mọc: {sunrise_dt.strftime('%H:%M, %d/%m/%Y')}")
        except Exception:
            lines.append(f"🌅 Mặt trời mọc: {sunrise}")

    if sunset:
        try:
            sunset_dt = datetime.datetime.fromisoformat(str(sunset))
            if sunset_dt.tzinfo is None:
                sunset_dt = sunset_dt.replace(tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
            else:
                sunset_dt = sunset_dt.astimezone(ZoneInfo("Asia/Ho_Chi_Minh"))
            lines.append(f"🌇 Mặt trời lặn: {sunset_dt.strftime('%H:%M, %d/%m/%Y')}")
        except Exception:
            lines.append(f"🌇 Mặt trời lặn: {sunset}")

    # Ghép dữ liệu thô thành text
    block_text = "\n".join(lines)

    # Giá trị chuẩn hóa
    values = {
        "status_text": status_text,

        # Nhiệt độ
        "avg_temperature": _round1(_to_float(avg_temp_day)),
        "avg_temperature_day": _round1(_to_float(avg_temp_day)),   # alias cho summary.py
        "temperature_min": _round1(_to_float(tmin)),
        "temperature_max": _round1(_to_float(tmax)),
        "temperature_2m_min_day": _round1(_to_float(tmin)),        # alias
        "temperature_2m_max_day": _round1(_to_float(tmax)),        # alias
        "diurnal_range": _round1(_to_float(diurnal_range)),
        "hourly_anomaly_ratio": _round1(_to_float(hourly_anomaly)),
        "temp_level": temp_level,

        # Mưa
        "rain_sum": rain_sum_val,
        "precipitation_sum_day": rain_sum_val,                     # alias
        "avg_precipitation_day": avg_precipitation_day,
        "rain_level": rain_level_text,
        "precipitation_probability_day": _round1(_to_float(precip_prob_day)),

        # Gió
        "avg_wind_speed": _round1(_to_float(avg_wspd)),
        "avg_wind_speed_day": _round1(_to_float(avg_wspd)),        # alias
        "wind_speed_max": _round1(_to_float(wind_speed_max)),
        "wind_gusts_max": _round1(_to_float(wind_gusts_max)),
        "wind_level": wind_level,
        "wind_level_desc": wind_level_desc,

        # Mây, sương
        "cloudcover": cloud_values["cloudcover"],
        "cloudcover_level": cloud_values["cloudcover_level"],
        "cloudcover_mean": cloud_values["cloudcover"],             # alias
        "dewpoint": cloud_values["dewpoint"],
        "dewpoint_level": cloud_values["dewpoint_level"],
        "dewpoint_mean": cloud_values["dewpoint"],                 # alias

        # Độ ẩm
        "humidity_day": _round1(_to_float(humidity_day)),
        "humidity_level": humidity_level,
        "adjusted_feels_by_humidity": _round1(_to_float(adjusted_feels_humidity)),

        # Áp suất
        "pressure_day": _round1(_to_float(pressure_day)),
        "pressure_level": pressure_level,

        # Bức xạ & UV
        "avg_solar_day": _round1(_to_float(avg_solar_day)) if avg_solar_day is not None else 0,
        "avg_solar": _round1(_to_float(avg_solar_day)) if avg_solar_day is not None else 0,   # alias
        "solar_sum_day": _round1(_to_float(solar_sum_day)) if solar_sum_day is not None else 0,
        "solar_level": solar_level if solar_level is not None else "🌙 Ban đêm, không có bức xạ",

        "avg_uv_day": _round1(_to_float(avg_uv_day)) if avg_uv_day is not None else 0,
        "uv_max_val": _round1(_to_float(uv_max_val)) if uv_max_val is not None else 0,
        "uv_max_day": _round1(_to_float(uv_max_val)) if uv_max_val is not None else 0,        # alias
        "uv_level_avg": uv_level_avg if uv_level_avg is not None else "🌙 Ban đêm, UV = 0",
        "uv_level_max": uv_level_max if uv_level_max is not None else "🌙 Ban đêm, UV = 0",

        # Mặt trời mọc/lặn
        "sunrise": sunrise_dt.strftime('%H:%M, %d/%m/%Y') if 'sunrise_dt' in locals() else sunrise,
        "sunset": sunset_dt.strftime('%H:%M, %d/%m/%Y') if 'sunset_dt' in locals() else sunset,
    }

    # Trả về text + values
    return block_text, values

