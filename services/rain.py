# services/rain.py
import datetime
from typing import Dict, Any, List, Optional

# -------------------------------
# Helpers
# -------------------------------
def _to_float(val: Any) -> Optional[float]:
    try:
        if val is None:
            return None
        return float(val)
    except Exception:
        return None

def _round1(val: Optional[float]) -> Optional[float]:
    return None if val is None else round(val, 1)

# -------------------------------
# Core rain logic
# -------------------------------
def compute_rain_intensity(rain: Any, avg_rain_hour: Any) -> Optional[float]:
    """Tỷ lệ lượng mưa tức thời so với trung bình giờ (x)."""
    r, ah = _to_float(rain), _to_float(avg_rain_hour)
    if r is None or ah is None or ah <= 0:
        return None
    return _round1(r / ah)

def classify_rain_level(rain: Any) -> Optional[str]:
    """Phân loại mức mưa theo ngưỡng mm/h (dùng giá trị gốc, không làm tròn)."""
    r = _to_float(rain)
    if r is None:
        return None
    if r >= 50.0:
        return "🌧️ Mưa rất lớn, nguy cơ ngập úng và lũ diện rộng."
    elif r >= 20.0:
        return "🌧️ Mưa lớn, cần cảnh giác ngập úng."
    elif r >= 5.0:
        return "🌦️ Mưa vừa, ảnh hưởng sinh hoạt ngoài trời."
    elif r > 0.0:
        return "☔ Mưa nhẹ, ít ảnh hưởng."
    else:
        return "🙂 Không mưa."

def interpret_rain_probability(prob: Any) -> Optional[str]:
    p = _to_float(prob)
    if p is None:
        return None
    if p >= 70:
        return "⚠️ Xác suất mưa cao, nên chuẩn bị áo mưa/ô."
    if p >= 40:
        return "ℹ️ Khả năng có mưa, cần theo dõi."
    return "✅ Khả năng mưa thấp."

# -------------------------------
# Rain summary (extended with daily probability)
# -------------------------------
def build_rain_summary(unified: Dict[str, Any], mode: str = "both") -> Dict[str, Any]:
    rain_now        = unified.get("precipitation_now")             # mm/h (tức thời)
    avg_rain_hour   = unified.get("precipitation_hourly")          # mm/h (trung bình giờ)
    rain_prob       = unified.get("precipitation_probability_now") # % tức thời
    rain_sum        = unified.get("precipitation_sum_day")         # mm (tổng ngày)
    avg_rain_day    = unified.get("precipitation_day")             # mm (trung bình ngày)
    rain_prob_day   = unified.get("precipitation_probability_day") # % trung bình ngày

    # --- Fallback cho tổng lượng mưa ngày ---
    if rain_sum is None:
        try:
            times = unified.get("hourly", {}).get("series", {}).get("time", [])
            precips = unified.get("hourly", {}).get("series", {}).get("precipitation", [])
            today_str = datetime.date.today().isoformat()
            today_precips = [
                _to_float(v) or 0.0
                for i, v in enumerate(precips)
                if i < len(times) and times[i].startswith(today_str)
            ]
            rain_sum = sum(today_precips) if today_precips else None
        except Exception:
            pass

    # --- Fallback cho trung bình ngày ---
    if avg_rain_day is None and rain_sum is not None:
        try:
            hours_count = len([
                t for t in unified.get("hourly", {}).get("series", {}).get("time", [])
                if t.startswith(datetime.date.today().isoformat())
            ])
            avg_rain_day = rain_sum / hours_count if hours_count > 0 else None
        except Exception:
            pass

    # --- Fallback cho xác suất mưa trung bình ngày ---
    if rain_prob_day is None:
        try:
            times = unified.get("hourly", {}).get("series", {}).get("time", [])
            probs = unified.get("hourly", {}).get("series", {}).get("precipitation_probability", [])
            today_str = datetime.date.today().isoformat()
            today_probs = [
                _to_float(v) or 0.0
                for i, v in enumerate(probs)
                if i < len(times) and times[i].startswith(today_str)
            ]
            if today_probs:
                rain_prob_day = sum(today_probs) / len(today_probs)
        except Exception:
            pass

    # --- Các tỷ lệ phân tích ---
    intensity_ratio_now    = compute_rain_intensity(rain_now, avg_rain_hour)
    intensity_ratio_hourly = None
    intensity_ratio_day    = None

    try:
        if avg_rain_hour is not None and avg_rain_day not in (None, 0):
            intensity_ratio_hourly = _round1(_to_float(avg_rain_hour) / _to_float(avg_rain_day))
    except Exception:
        pass

    try:
        if avg_rain_day is not None and rain_sum not in (None, 0):
            intensity_ratio_day = round(float(avg_rain_day) / float(rain_sum), 3)
    except Exception:
        pass

    level_text = classify_rain_level(rain_now)
    prob_text  = interpret_rain_probability(rain_prob)
    prob_day_text = interpret_rain_probability(rain_prob_day)

    def fmt(v, unit=""):
        fv = _round1(_to_float(v))
        return "—" if fv is None else f"{fv}{unit}"

    lines: List[str] = []

    # Khối tức thời
    if mode in ("current", "both"):
        lines.append(f"☔ Lượng mưa hiện tại: {fmt(rain_now, ' mm/h')}")
        if intensity_ratio_now is not None:
            lines.append(f"⏱️ Cường độ mưa hiện tại: {intensity_ratio_now}× so với trung bình giờ")
        if prob_text:
            lines.append(f"📊 {prob_text}")
        if level_text:
            lines.append(level_text)

    # Khối theo giờ
    if mode in ("hourly", "both"):
        lines.append(f"🌦️ Lượng mưa trung bình theo giờ: {fmt(avg_rain_hour, ' mm/h')}")
        if intensity_ratio_hourly is not None:
            lines.append(f"📈 Trung bình giờ so với trung bình ngày: {intensity_ratio_hourly}×")

    # Khối trong ngày
    if mode in ("daily", "both"):
        lines.append(f"🌧️ Tổng lượng mưa ngày: {fmt(rain_sum, ' mm')}")
        lines.append(f"🌦️ Lượng mưa trung bình ngày: {fmt(avg_rain_day, ' mm')}")
        if rain_prob_day is not None:
            prob_val = int(round(_to_float(rain_prob_day)))
            lines.append(f"📊 Xác suất mưa trung bình ngày: {prob_val}% ({prob_day_text if prob_day_text else '—'})")
        if intensity_ratio_day is not None:
            lines.append(f"📉 Trung bình ngày so với tổng ngày: {intensity_ratio_day}")

    return {
        "values": {
            "precipitation_now": _round1(_to_float(rain_now)),
            "precipitation_hourly": _round1(_to_float(avg_rain_hour)),
            "precipitation_probability_now": _round1(_to_float(rain_prob)),
            "precipitation_probability_day": _round1(_to_float(rain_prob_day)),  # ✅ thêm vào values
            "intensity_ratio_now": intensity_ratio_now,
            "intensity_ratio_hourly": intensity_ratio_hourly,
            "intensity_ratio_day": intensity_ratio_day,
            "rain_level": level_text,
            "precipitation_sum_day": _round1(_to_float(rain_sum)),
            "precipitation_day": _round1(_to_float(avg_rain_day)),
        },
        "lines": lines,
    }

# -------------------------------
# Rain block builder (extended)
# -------------------------------
def build_rain_block(unified: Dict[str, Any], mode: str = "both") -> str:
    """
    Xây dựng khối hiển thị mưa theo mode:
      - 'current': chỉ hiển thị mưa tức thời
      - 'hourly' : chỉ hiển thị mưa trung bình theo giờ
      - 'daily'  : chỉ hiển thị mưa trong ngày
      - 'both'   : hiển thị tất cả
    Bao gồm thêm các tỷ lệ phân tích sâu hơn.
    """
    summary = build_rain_summary(unified, mode=mode)
    block_text = "\n".join(summary["lines"])
    return block_text