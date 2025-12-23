# services/cloud_dew.py
from typing import Any, Optional

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
# Phân loại độ che phủ mây
# -------------------------------
def classify_cloudcover(cloudcover: Any) -> Optional[str]:
    """Phân loại độ che phủ mây theo %."""
    c = _to_float(cloudcover)
    if c is None:
        return None
    if c >= 90:
        return "☁️ Trời u ám, mây dày đặc."
    if c >= 60:
        return "☁️ Nhiều mây, ánh sáng mặt trời hạn chế."
    if c >= 30:
        return "⛅ Ít mây, trời khá thoáng."
    return "☀️ Trời quang đãng, hầu như không có mây."

# -------------------------------
# Phân loại điểm sương
# -------------------------------
def classify_dewpoint(dewpoint: Any) -> Optional[str]:
    """Phân loại điểm sương theo °C, phản ánh độ ẩm thực tế."""
    d = _to_float(dewpoint)
    if d is None:
        return None
    if d >= 24:
        return "💧 Điểm sương rất cao, không khí ngột ngạt, dễ cảm thấy oi bức."
    if d >= 20:
        return "💧 Điểm sương cao, không khí ẩm, dễ đổ mồ hôi."
    if d >= 16:
        return "💧 Điểm sương trung bình, không khí dễ chịu."
    if d >= 10:
        return "💧 Điểm sương thấp, không khí khô ráo."
    return "💧 Điểm sương rất thấp, không khí khô hanh."

# -------------------------------
# Hàm tổng hợp cho hiển thị
# -------------------------------
def build_cloud_dew_summary(cloudcover: Any, dewpoint: Any) -> dict:
    cloud_text = classify_cloudcover(cloudcover)
    dew_text = classify_dewpoint(dewpoint)

    values = {
        "cloudcover": _round1(_to_float(cloudcover)),
        "cloudcover_level": cloud_text,
        "dewpoint": _round1(_to_float(dewpoint)),
        "dewpoint_level": dew_text,
    }

    lines = []
    if values["cloudcover"] is not None:
        lines.append(
            f"☁️ Độ che phủ mây trung bình: {values['cloudcover']}% "
            f"({values['cloudcover_level'] if values['cloudcover_level'] else '—'})"
        )
    if values["dewpoint"] is not None:
        lines.append(
            f"💧 Điểm sương trung bình: {values['dewpoint']}°C "
            f"({values['dewpoint_level'] if values['dewpoint_level'] else '—'})"
        )

    return {
        "values": values,
        "lines": lines
    }