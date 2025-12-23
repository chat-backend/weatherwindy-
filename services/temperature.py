# services/temperature.py
from typing import Dict, Any, List, Optional, Tuple

def _to_float(val: Any) -> Optional[float]:
    try:
        if val is None:
            return None
        return float(val)
    except Exception:
        return None

def _round1(val: Optional[float]) -> Optional[float]:
    return None if val is None else round(val, 1)

def compute_avg_temp(avg_temp: Any = None, tmin: Any = None, tmax: Any = None) -> Optional[float]:
    at = _to_float(avg_temp)
    if at is not None:
        return _round1(at)
    vmin, vmax = _to_float(tmin), _to_float(tmax)
    if vmin is not None and vmax is not None:
        return _round1((vmin + vmax) / 2.0)
    return None

def compute_adjusted_feels(temp: Any, feels: Any, wind: Any = None, humidity: Any = None) -> Optional[float]:
    t, f, w, h = _to_float(temp), _to_float(feels), _to_float(wind), _to_float(humidity)
    if t is None or f is None:
        return None

    adjusted = f
    if w is not None and w > 2:
        reduction = w / 4.0
        if t is not None and t > 20:
            reduction = min(reduction, 6.0)
        adjusted -= reduction

    if t is not None and t <= 22 and h is not None and h >= 85:
        adjusted -= 1.0

    return _round1(adjusted)

def compute_feels_gap(temp: Any, feels: Any, wind: Any = None, humidity: Any = None) -> Optional[float]:
    adj_feels = compute_adjusted_feels(temp, feels, wind, humidity)
    t = _to_float(temp)
    if t is None or adj_feels is None:
        return None
    return _round1(adj_feels - t)

def compute_diurnal_range(tmin: Any, tmax: Any) -> Optional[float]:
    vmin, vmax = _to_float(tmin), _to_float(tmax)
    if vmin is None or vmax is None:
        return None
    return _round1(vmax - vmin)

def compute_hourly_anomaly(temp: Any, avg_temp_hour: Any) -> Optional[float]:
    t, ah = _to_float(temp), _to_float(avg_temp_hour)
    if t is None or ah is None or ah == 0:
        return None
    return _round1(t / ah)

def classify_temp_level(temp: Any, region: str = "north") -> Optional[str]:
    """
    Phân loại mức độ nhiệt độ theo vùng miền:
      - region="north": Miền Bắc (quen chịu lạnh, 18°C vẫn coi là mát mẻ)
      - region="central_south": Miền Trung/Nam (18°C đã coi là lạnh)
    """
    t = _to_float(temp)
    if t is None:
        return None

    if t >= 40:
        return "🔥 Cực kỳ nóng (≥40°C)"
    if t >= 35:
        return "🌡️ Rất nóng (≥35°C)"
    if t >= 30:
        return "☀️ Nóng (30–34°C)"
    if t >= 25:
        return "🙂 Ấm áp (25–29°C)"

    if region == "north":
        # Miền Bắc: 18–24°C coi là mát mẻ, ≤17°C mới là lạnh
        if t >= 18:
            return "🌤️ Mát mẻ (18–24°C)"
        if t >= 10:
            return "🥶 Lạnh (10–17°C)"
        if t > 0:
            return "❄️ Rất lạnh (1–9°C)"
        return "🧊 Cực lạnh (≤0°C)"
    else:
        # Miền Trung/Nam: 20–24°C coi là mát mẻ, ≤19°C đã là lạnh
        if t >= 20:
            return "🌤️ Mát mẻ (20–24°C)"
        if t >= 15:
            return "🥶 Lạnh (15–19°C)"
        if t > 0:
            return "❄️ Rất lạnh (1–14°C)"
        return "🧊 Cực lạnh (≤0°C)"

def build_temperature_summary(unified: Dict[str, Any], region: str = "north") -> Dict[str, Any]:
    # Naming khớp tuyệt đối với unified từ helpers
    temp   = unified.get("temperature_now")
    feels  = unified.get("apparent_temperature_now")
    tmin   = unified.get("temperature_2m_min_day")
    tmax   = unified.get("temperature_2m_max_day")
    avg_t  = compute_avg_temp(unified.get("temperature_day"), tmin, tmax)
    avg_t_hour = unified.get("temperature_hourly")
    wind   = unified.get("wind_speed_now")
    humidity = unified.get("humidity_now")

    dr = compute_diurnal_range(tmin, tmax)
    adj_feels = compute_adjusted_feels(temp, feels, wind, humidity)
    gap = compute_feels_gap(temp, feels, wind, humidity)
    anomaly = compute_hourly_anomaly(temp, avg_t_hour)
    level = classify_temp_level(temp, region=region)

    def _fmt(v, unit="°C"):
        return "—" if v is None else f"{_round1(_to_float(v))}{unit}"

    lines: List[str] = [
        f"🌡️ Nhiệt độ hiện tại: {_fmt(temp)}",
        f"🙂 Cảm giác thực tế (điều chỉnh): {_fmt(adj_feels)}",
        f"📝 Nhiệt độ trung bình ngày: {_fmt(avg_t)}",
        f"📈 Dao động ngày: {_fmt(tmin)} / {_fmt(tmax)} (biên độ {_fmt(dr)})",
        f"⏱️ Lệch theo giờ: {('—' if anomaly is None else f'{anomaly}×')} (so với trung bình giờ)",
    ]
    if level:
        lines.append(f"🏷️ Mức độ: {level}")

    return {
        "values": {
            "temperature_now": _round1(_to_float(temp)),
            "apparent_temperature_now": _round1(_to_float(feels)),
            "adjusted_apparent_temperature": adj_feels,
            "temperature_day": avg_t,
            "temperature_2m_min_day": _round1(_to_float(tmin)),
            "temperature_2m_max_day": _round1(_to_float(tmax)),
            "diurnal_range": dr,
            "hourly_anomaly_ratio": anomaly,
            "feels_gap": gap,
            "temp_level": level,
        },
        "lines": lines,
    }

def build_temperature_block(unified: Dict[str, Any], region: str = "north") -> str:
    summary = build_temperature_summary(unified, region=region)
    return "\n".join(summary["lines"])