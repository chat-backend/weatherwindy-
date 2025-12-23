# services/visibility.py
from typing import Optional, Dict, Any
import datetime

def _to_float(val: Any) -> Optional[float]:
    """Chuyển đổi giá trị sang float an toàn."""
    try:
        if val is None:
            return None
        return float(val)
    except Exception:
        return None

def _round1(val: Optional[float]) -> Optional[float]:
    """Làm tròn 1 chữ số thập phân."""
    return None if val is None else round(val, 1)

# -------------------------------
# Phân loại tầm nhìn (visibility)
# -------------------------------
def classify_visibility(vis_km: Optional[float]) -> str:
    """
    Phân loại mức độ tầm nhìn theo km.
    - vis_km: tầm nhìn (km)
    """
    if vis_km is None:
        return "—"

    vis_km = _round1(vis_km)  # chuẩn hóa trước khi phân loại

    if vis_km >= 10:
        return "👀 Tầm nhìn xa, điều kiện lý tưởng."
    elif 5 <= vis_km < 10:
        return "👀 Tầm nhìn tốt, ít ảnh hưởng giao thông."
    elif 2 <= vis_km < 5:
        return "⚠️ Tầm nhìn hạn chế, cần thận trọng khi lái xe."
    elif 1 <= vis_km < 2:
        return "⚠️ Tầm nhìn kém, nguy hiểm cho giao thông."
    else:  # < 1 km
        return "🚨 Tầm nhìn rất kém (<1 km), nguy cơ cao tai nạn."

# -------------------------------
# Hàm phân tích tổng quan tầm nhìn
# -------------------------------
def analyze_visibility(daily: Dict[str, Any], hourly: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân tích tầm nhìn từ dữ liệu daily/hourly.
    Trả về dict gồm giá trị và phân loại.
    """
    # Daily visibility (mét → km)
    vis_day = _to_float(daily.get("visibility_day"))
    if vis_day is not None:
        vis_day = vis_day / 1000.0

    # Hourly visibility tức thời (mét → km)
    vis_now = _to_float(hourly.get("visibility_now"))
    if vis_now is not None:
        vis_now = vis_now / 1000.0

    # Trung bình theo ngày từ hourly series
    vis_avg_day = None
    try:
        times = hourly.get("series", {}).get("time", [])
        # kiểm tra cả hai khả năng: visibility_hourly hoặc series["visibility"]
        vis_series = hourly.get("visibility_hourly") or hourly.get("series", {}).get("visibility", [])
        today_str = datetime.date.today().isoformat()

        today_vals = [
            _to_float(v) / 1000.0 for i, v in enumerate(vis_series)
            if i < len(times)
            and isinstance(times[i], str)
            and times[i].startswith(today_str)
            and _to_float(v) is not None
        ]
        if today_vals:
            vis_avg_day = _round1(sum(today_vals) / len(today_vals))
    except Exception:
        vis_avg_day = None

    # Ưu tiên daily → hourly_avg → hourly_now
    vis_val = None
    source = None
    if vis_day is not None:
        vis_val = vis_day
        source = "daily"
    elif vis_avg_day is not None:
        vis_val = vis_avg_day
        source = "hourly_avg"
    elif vis_now is not None:
        vis_val = vis_now
        source = "hourly_now"

    vis_val_round = _round1(vis_val)
    vis_level_text = classify_visibility(vis_val)

    return {
        "visibility_day": _round1(vis_day),
        "visibility_avg_day": vis_avg_day,
        "visibility_now": _round1(vis_now),
        "visibility_val": vis_val_round,
        "visibility_level": vis_level_text,
        "visibility_source": source,  # nguồn dữ liệu được chọn
    }