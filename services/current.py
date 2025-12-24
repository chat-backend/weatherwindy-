# services/current.py
import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Tuple, Optional

from services.temperature import (
    compute_avg_temp, compute_feels_gap, compute_diurnal_range,
    compute_hourly_anomaly, classify_temp_level, compute_adjusted_feels
)
from services.rain import compute_rain_intensity, classify_rain_level, interpret_rain_probability
from services.wind import classify_wind_beaufort, classify_wind_level, interpret_gust, wind_direction_to_text
from services.cloud_dew import build_cloud_dew_summary
from services.visibility import classify_visibility
from services.humidity import classify_humidity, adjust_feels_by_humidity
from services.pressure import classify_pressure
from services.solar_uv import classify_solar, classify_uv, _is_night

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
# Khối tình hình hiện tại
# -------------------------------
def build_current_block(
    unified: Dict[str, Any],
    status_text: str,
    wind_unit: str = "m/s",
    region: str = "north"
) -> Tuple[str, Dict[str, Any]]:

    # Fallback cho dữ liệu tức thời
    temp   = unified.get("temperature_now") or unified.get("temperature_hourly") or unified.get("temperature_day")
    feels  = unified.get("apparent_temperature_now") or unified.get("apparent_temperature_hourly")
    wspd   = unified.get("wind_speed_now") or unified.get("wind_speed_hourly") or unified.get("avg_wind_speed_day")
    gust   = unified.get("gust_now") or unified.get("gust_hourly")
    rh     = unified.get("humidity_now") or unified.get("humidity_hourly") or unified.get("humidity_day")
    pmsl   = unified.get("pressure_now") or unified.get("pressure_hourly") or unified.get("pressure_day")
    solar  = unified.get("solar_radiation_now") or unified.get("solar_radiation_hourly")
    uv_now = unified.get("uv_index_now") or unified.get("uv_index_hourly")

    # Mưa tức thời: fallback sang chuỗi hourly nếu thiếu
    rain   = unified.get("precipitation_now")
    if rain is None:
        series_precip = unified.get("hourly", {}).get("series", {}).get("precipitation", [])
        series_time   = unified.get("hourly", {}).get("series", {}).get("time", [])
        if series_precip and series_time:
            try:
                now_local = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
                now_str = now_local.strftime("%Y-%m-%dT%H:00")
                if now_str in series_time:
                    idx = series_time.index(now_str)
                    rain = series_precip[idx]
            except Exception:
                pass

    rain_prob = unified.get("precipitation_probability_now") or unified.get("precipitation_probability_hourly") or unified.get("precipitation_probability_day")
    wind_dir = unified.get("wind_direction_now")
    visibility = unified.get("visibility_now")
    cloudcover = unified.get("cloudcover_now") or unified.get("cloudcover_hourly")
    dewpoint = unified.get("dewpoint_now") or unified.get("dewpoint_hourly")

    # Daily để tính toán thêm
    tmin   = unified.get("temperature_2m_min_day")
    tmax   = unified.get("temperature_2m_max_day")

    # Nhiệt độ
    avg_temp_day = compute_avg_temp(unified.get("temperature_day"), tmin, tmax)
    adj_feels = compute_adjusted_feels(temp, feels, wspd, rh)
    feels_gap = compute_feels_gap(temp, feels, wspd, rh)
    diurnal_range = compute_diurnal_range(tmin, tmax)
    hourly_anomaly = compute_hourly_anomaly(temp, unified.get("temperature_hourly"))
    temp_level = classify_temp_level(temp, region=region)

    # --- MƯA ---
    intensity_ratio = unified.get("intensity_ratio_now")
    if intensity_ratio is None:
        intensity_ratio = compute_rain_intensity(rain, unified.get("precipitation_hourly"))

    rain_level_text = classify_rain_level(rain)
    rain_prob_text  = interpret_rain_probability(rain_prob)

    # Gió
    wind_level = classify_wind_beaufort(wspd)
    wind_level_desc = classify_wind_level(wspd, gust, region=region)
    gust_text = interpret_gust(gust, wspd, region=region)

    # Mây, sương
    cloud_dew_summary = build_cloud_dew_summary(cloudcover, dewpoint)
    cloud_values = cloud_dew_summary["values"]

    # Tầm nhìn
    vis_val = None
    vis_level_text = None
    if visibility is not None:
        vis_val = _to_float(visibility)
        if vis_val is not None:
            vis_level_text = classify_visibility(_round1(vis_val / 1000))

    # Độ ẩm  
    humidity_level = classify_humidity(rh)
    adjusted_feels_humidity = adjust_feels_by_humidity(temp, feels, rh, region=region)

    # Áp suất
    pressure_level = classify_pressure(pmsl, region=region)

    # Bức xạ/UV
    now_local = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    is_night = _is_night(now_local)

    solar_val = _round1(_to_float(solar)) if not is_night else None
    uv_val    = _round1(_to_float(uv_now)) if not is_night else None

    # Hiển thị
    lines: List[str] = []
    lines.append(f"🌤️ Trạng thái: {status_text or '—'}")

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

    # Nhiệt độ, mưa, gió, mây, sương, tầm nhìn, độ ẩm, áp suất
    if temp is not None:
        lines.append(f"🌡️ Nhiệt độ hiện tại: {fmt(_round1(_to_float(temp)), '°C')}")
    if adj_feels is not None:
        lines.append(f"🙂 Cảm giác thực tế: {fmt(_round1(_to_float(adj_feels)), '°C')}")
    if hourly_anomaly is not None:
        lines.append(f"⏱️ So với trung bình giờ: {fmt(_round1(_to_float(hourly_anomaly)), '×')}")
    if temp_level:
        lines.append(f"🏷️ Mức độ nhiệt độ: {temp_level}")

    if rain is not None:
        lines.append(f"🌧️ Lượng mưa hiện tại: {fmt(_round1(_to_float(rain)), ' mm/h')}")
    if rain_prob is not None:
        lines.append(f"📊 Xác suất mưa hiện tại: {fmt(_round1(_to_float(rain_prob)), '%')} ({rain_prob_text or '—'})")
    if intensity_ratio is not None:
        lines.append(f"⏱️ Cường độ mưa hiện tại: {fmt(_round1(_to_float(intensity_ratio)), '×')} so với trung bình giờ")
    if rain_level_text:
        lines.append(f"🏷️ Mức độ mưa: {rain_level_text}")

    if wspd is not None:
        wspd_val = _round1(_to_float(wspd))
        gust_val = _round1(_to_float(gust))
        wspd_kmh = _round1(_to_float(wspd) * 3.6) if wspd is not None else None
        gust_kmh = _round1(_to_float(gust) * 3.6) if gust is not None else None
        lines.append(f"💨 Gió hiện tại: {fmt(wspd_val, f' {wind_unit}')} ({fmt(wspd_kmh, ' km/h')}) (giật {fmt(gust_val, f' {wind_unit}')}, {fmt(gust_kmh, ' km/h')})")
    if wind_level is not None:
        lines.append(f"🌀 Cấp gió Beaufort: {wind_level}")
    if gust_text:
        lines.append(gust_text)
    if wind_level_desc:
        lines.append(f"🍃 Mức độ gió: {wind_level_desc}")
    if wind_dir is not None:
        lines.append(f"↔️ Hướng gió: {fmt(wind_dir, '°')} ({wind_direction_to_text(wind_dir)})")

    if cloud_values["cloudcover"] is not None:
        lines.append(f"☁️ Độ che phủ mây trung bình: {cloud_values['cloudcover']}% ({cloud_values['cloudcover_level'] or '—'})")
    if cloud_values["dewpoint"] is not None:
        lines.append(f"🌫️ Điểm sương trung bình: {cloud_values['dewpoint']}°C ({cloud_values['dewpoint_level'] or '—'})")

    # Tầm nhìn
    if vis_val is not None:
        vis_km = _round1(vis_val / 1000.0)  # đổi từ mét sang km
        lines.append(f"👀 Tầm nhìn hiện tại: {fmt(vis_km, ' km')}")
        if vis_level_text:
            lines.append(f"🏷️ Mức độ tầm nhìn: {vis_level_text}")
    else:
        lines.append("👀 Tầm nhìn hiện tại: — km")
        lines.append("🏷️ Mức độ tầm nhìn: —")

    if rh is not None:
        lines.append(f"💧 Độ ẩm hiện tại: {fmt(_round1(_to_float(rh)), '%')} ({humidity_level or '—'})")
    if adjusted_feels_humidity is not None:
        lines.append(f"🤔 Cảm giác thực tế (điều chỉnh theo độ ẩm): {fmt(_round1(_to_float(adjusted_feels_humidity)), '°C')}")

    if pmsl is not None:
        lines.append(f"⚖️ Áp suất hiện tại: {fmt(_round1(_to_float(pmsl)), ' hPa')} ({pressure_level or '—'})")

    # --- BỨC XẠ / UV ---
    solar_level = None
    uv_level_now = None

    if is_night:
        # Ban đêm: luôn gán giá trị mặc định
        solar_val = 0
        uv_val = 0
        lines.append("🔆 Bức xạ mặt trời hiện tại: 0 W/m² (🌙 Ban đêm)")
        lines.append("☀️ UV hiện tại: 0 (🌙 Ban đêm)")
    else:
        # Ban ngày: xử lý an toàn
        if solar_val is not None:
            solar_level = classify_solar(
                solar_val,
                region=region,
                cloudcover=cloudcover,
                now=now_local
            )
            lines.append(
                f"🔆 Bức xạ mặt trời hiện tại: {fmt(solar_val, ' W/m²')} ({solar_level or '—'})"
            )
        else:
            lines.append("🔆 Bức xạ mặt trời hiện tại: — W/m²")

        if uv_val is not None:
            uv_level_now = classify_uv(
                uv_val,
                precipitation=rain,
                cloudcover=cloudcover,
                now=now_local
            )
            lines.append(
                f"☀️ UV hiện tại: {fmt(uv_val)} ({uv_level_now or '—'})"
            )
        else:
            lines.append("☀️ UV hiện tại: —")

    # Ghép dữ liệu thô thành text
    block_text = "\n".join(lines)

    # Giá trị chuẩn hóa
    values = {
        "status_text": status_text,
        "temperature_now": _round1(_to_float(temp)),
        "apparent_temperature_now": _round1(_to_float(feels)),
        "adjusted_feels": _round1(_to_float(adj_feels)),
        "feels_gap": _round1(_to_float(feels_gap)),
        "diurnal_range": _round1(_to_float(diurnal_range)),
        "hourly_anomaly_ratio": _round1(_to_float(hourly_anomaly)),
        "avg_temperature_day": _round1(_to_float(avg_temp_day)),
        "temperature_2m_min_day": _round1(_to_float(tmin)),
        "temperature_2m_max_day": _round1(_to_float(tmax)),
        "temp_level": temp_level,
        "rain_now": _round1(_to_float(rain)),
        "rain_probability_now": _round1(_to_float(rain_prob)),
        "intensity_ratio_now": _round1(_to_float(intensity_ratio)),
        "rain_level": rain_level_text,
        "wind_speed_now": _round1(_to_float(wspd)),
        "gust_now": _round1(_to_float(gust)),
        "wind_level": wind_level,
        "wind_level_desc": wind_level_desc,
        "gust_text": gust_text,
        "wind_direction_now": _round1(_to_float(wind_dir)),
        "wind_direction_text": wind_direction_to_text(wind_dir) if wind_dir is not None else None,
        "cloudcover_now": cloud_values["cloudcover"],
        "cloudcover_level": cloud_values["cloudcover_level"],
        "dewpoint_now": cloud_values["dewpoint"],
        "dewpoint_level": cloud_values["dewpoint_level"],
        "visibility_now_km": _round1(vis_val / 1000) if vis_val is not None else None,
        "visibility_level": vis_level_text,
        "humidity_now": _round1(_to_float(rh)),
        "humidity_level": humidity_level,
        "adjusted_feels_by_humidity": _round1(_to_float(adjusted_feels_humidity)),
        "pressure_now": _round1(_to_float(pmsl)),
        "pressure_level": pressure_level,
        "solar_now": solar_val if solar_val is not None else 0,
        "solar_level": solar_level,
        "uv_now": uv_val if uv_val is not None else 0,
        "uv_level_now": uv_level_now,
    }

    # Trả về text + values
    return block_text, values