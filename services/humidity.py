# services/humidity.py
from typing import Dict, Any, List, Tuple, Optional

# -------------------------------
# Chuẩn hóa dữ liệu
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
# Phân loại mức độ độ ẩm
# -------------------------------
def classify_humidity(rh: Any) -> Optional[str]:
    """Phân loại độ ẩm theo ngưỡng %."""
    r = _to_float(rh)
    if r is None:
        return None
    if r >= 90:
        return "💧 Độ ẩm rất cao (≥90%), dễ nồm ẩm, không khí bí, đồ đạc ẩm mốc."
    if r >= 70:
        return "💧 Độ ẩm cao (≥70%), cảm giác ẩm ướt, khó thoát mồ hôi."
    if r <= 30:
        return "🔥 Độ ẩm thấp (≤30%), dễ khô da, tăng nguy cơ kích ứng."
    return "🙂 Độ ẩm ở mức trung bình, tương đối dễ chịu."

# -------------------------------
# Điều chỉnh cảm giác theo độ ẩm và vùng miền
# -------------------------------
def adjust_feels_by_humidity(temp: Any, feels: Any, humidity: Any, region: str = "north") -> Optional[float]:
    """Điều chỉnh cảm giác thực tế dựa trên độ ẩm và vùng miền."""
    t, f, h = _to_float(temp), _to_float(feels), _to_float(humidity)
    if t is None or f is None:
        return None

    adjusted = f

    if region == "north":
        # Miền Bắc: khí hậu ẩm, dễ nồm lạnh
        if h is not None and h >= 90 and t is not None and t <= 22:
            adjusted -= 1.5
        if h is not None and h >= 70 and t is not None and t > 25:
            adjusted += 0.5
        if h is not None and h <= 30:
            adjusted -= 0.5
    else:
        # Miền Trung/Nam: khí hậu khô nóng hơn
        if h is not None and h >= 90 and t is not None and t <= 22:
            adjusted -= 1.0
        if h is not None and h >= 70 and t is not None and t > 25:
            adjusted += 1.0
        if h is not None and h <= 30:
            adjusted -= 0.3

    return _round1(adjusted)

# -------------------------------
# Hàm tổng hợp cho bulletin
# -------------------------------
def build_humidity_summary(unified: Dict[str, Any], region: str = "north") -> Dict[str, Any]:
    rh_now = unified.get("humidity")
    avg_rh = unified.get("avg_humidity")
    temp   = unified.get("temperature")
    feels  = unified.get("apparent_temperature")

    level_text = classify_humidity(rh_now)
    adj_feels = adjust_feels_by_humidity(temp, feels, rh_now, region=region)

    # Chuỗi hiển thị
    lines: List[str] = []
    def fmt(v, unit="%"):
        return "—" if _to_float(v) is None else f"{_round1(_to_float(v))}{unit}"

    lines.append(f"💧 Độ ẩm hiện tại: {fmt(rh_now)}")
    lines.append(f"💧 Độ ẩm trung bình ngày: {fmt(avg_rh)}")
    if level_text:
        lines.append(level_text)
    if adj_feels is not None:
        lines.append(f"🤔 Cảm giác thực tế (điều chỉnh theo độ ẩm): {adj_feels}°C")

    return {
        "values": {
            "humidity_now": _round1(_to_float(rh_now)),
            "avg_humidity": _round1(_to_float(avg_rh)),
            "humidity_level": level_text,
            "adjusted_feels_by_humidity": adj_feels,
        },
        "lines": lines,
    }

# -------------------------------
# API chính: tạo đoạn độ ẩm cho bulletin
# -------------------------------
def build_humidity_block(unified: Dict[str, Any], region: str = "north") -> str:
    summary = build_humidity_summary(unified, region=region)
    block_text = "\n".join(summary["lines"])
    return block_text