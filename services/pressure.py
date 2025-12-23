# services/pressure.py
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
# Phân loại mức độ áp suất
# -------------------------------
def classify_pressure(pmsl: Any, region: str = "north") -> Optional[str]:
    """Phân loại áp suất khí quyển theo ngưỡng hPa, có xét vùng miền."""
    p = _to_float(pmsl)
    if p is None:
        return None

    if region == "north":
        if p >= 1025:
            return "⚖️ Áp suất cao (≥1025 hPa), thời tiết thường ổn định, trời quang."
        if p <= 1000:
            return "⚠️ Áp suất thấp (≤1000 hPa), dễ xuất hiện mưa, dông hoặc thời tiết bất ổn."
    else:  # central_south
        if p >= 1020:  # ngưỡng thấp hơn một chút
            return "⚖️ Áp suất cao (≥1020 hPa), thời tiết thường ổn định."
        if p <= 1005:  # ngưỡng cao hơn một chút
            return "⚠️ Áp suất thấp (≤1005 hPa), dễ xuất hiện mưa, dông."
    return "🙂 Áp suất ở mức trung bình, thời tiết tương đối ổn định."

# -------------------------------
# Hàm tổng hợp cho bulletin 
# -------------------------------
def build_pressure_summary(unified: Dict[str, Any], region: str = "north") -> Dict[str, Any]:
    p_now = unified.get("pressure")
    p_avg = unified.get("avg_pressure")

    level_text = classify_pressure(p_now, region=region)

    # Chuỗi hiển thị
    lines: List[str] = []
    def fmt(v, unit=" hPa"):
        return "—" if _to_float(v) is None else f"{_round1(_to_float(v))}{unit}"

    lines.append(f"⚖️ Áp suất hiện tại: {fmt(p_now)}")
    lines.append(f"⚖️ Áp suất trung bình ngày: {fmt(p_avg)}")
    if level_text:
        lines.append(level_text)

    return {
        "values": {
            "pressure_now": _round1(_to_float(p_now)),
            "avg_pressure": _round1(_to_float(p_avg)),
            "pressure_level": level_text,   # ✅ đồng bộ với current/overview
        },
        "lines": lines,
    }

# -------------------------------
# API chính: tạo đoạn áp suất cho bulletin
# -------------------------------
def build_pressure_block(unified: Dict[str, Any], region: str = "north") -> str:
    summary = build_pressure_summary(unified, region=region)
    # Ghép các dòng hiển thị thành block
    block_text = "\n".join(summary["lines"])
    return block_text