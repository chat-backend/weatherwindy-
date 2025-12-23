# services/solar_uv.py
from typing import Dict, Any, List, Optional
import datetime

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
# Kiểm tra ban ngày / ban đêm
# -------------------------------
def _is_night(now: Optional[datetime.datetime] = None) -> bool:
    if now is None:
        now = datetime.datetime.now()
    hour = now.hour
    return hour < 6 or hour >= 18   # giả định: 6h–18h là ban ngày

# -------------------------------
# Phân loại mức độ bức xạ mặt trời
# -------------------------------
def classify_solar(solar: Any, region: str = "north", cloudcover: Any = None, now: Optional[datetime.datetime] = None) -> Optional[str]:
    if _is_night(now):
        return "🌙 Ban đêm, không có bức xạ mặt trời."

    s = _to_float(solar)
    if s is None or s < 0:
        return None

    cc = _to_float(cloudcover)
    if cc is not None:
        if cc >= 90:
            return "🔆 Bức xạ mặt trời rất thấp do mây dày đặc."
        elif cc >= 70:
            return "🔆 Bức xạ mặt trời thấp do mây che phủ nhiều."

    if region == "north":
        if s >= 800:
            return "🔆 Bức xạ mặt trời rất mạnh (≥800 W/m²), trời nắng gắt."
        if s >= 400:
            return "🔆 Bức xạ mặt trời trung bình (400–800 W/m²)."
        return "🔆 Bức xạ mặt trời yếu (<400 W/m²)."
    else:
        if s >= 700:
            return "🔆 Bức xạ mặt trời mạnh (≥700 W/m²)."
        if s >= 350:
            return "🔆 Bức xạ mặt trời trung bình (350–700 W/m²)."
        return "🔆 Bức xạ mặt trời yếu (<350 W/m²)."

# -------------------------------
# Phân loại mức độ UV
# -------------------------------
def classify_uv(uv: Any, precipitation: Any = None, cloudcover: Any = None, now: Optional[datetime.datetime] = None) -> Optional[str]:
    if _is_night(now):
        return "🌙 Ban đêm, chỉ số UV bằng 0."

    u = _to_float(uv)
    if u is None or u < 0:
        return None

    # Giảm UV do mưa và mây (cộng dồn)
    reduction = 0
    rain = _to_float(precipitation)
    cc = _to_float(cloudcover)
    if rain is not None and rain > 0:
        reduction += 2
    if cc is not None:
        if cc >= 90:
            reduction += 2
        elif cc >= 70:
            reduction += 1
    u = max(0, u - reduction)

    # Chuẩn WHO/EPA
    if u >= 11:
        return "☀️ UV cực đoan (≥11), tránh nắng hoàn toàn."
    elif u >= 8:
        return "☀️ UV rất cao (8–10), cần bảo vệ da và mắt."
    elif u >= 6:
        return "☀️ UV cao (6–7), nên dùng kem chống nắng."
    elif u >= 3:
        return "ℹ️ UV trung bình (3–5), cần lưu ý khi ra ngoài lâu."
    else:
        return "🙂 UV thấp (0–2), an toàn khi ra ngoài."

# -------------------------------
# Hàm phụ định dạng bức xạ và UV
# -------------------------------
def _format_solar_sum(val: Any) -> str:
    v = _to_float(val)
    if v is None:
        return "0 Wh/m² (không có số liệu)"
    v = _round1(v)
    # Luôn coi là tổng tích lũy: Wh hoặc kWh
    if v < 1000:
        return f"{v} Wh/m² (tổng tích lũy ngày)"
    else:
        kwh = v / 1000.0
        return f"{_round1(kwh)} kWh/m² (tổng tích lũy ngày)"

def _format_uv_avg(val: Any) -> str:
    u = _to_float(val)
    if u is None:
        return "0 (không có số liệu)"
    u = _round1(u)
    if u < 3:
        return f"{u} (🙂 UV thấp)"
    elif u < 6:
        return f"{u} (ℹ️ UV trung bình)"
    elif u < 8:
        return f"{u} (⚠️ UV cao)"
    elif u < 11:
        return f"{u} (🚨 UV rất cao)"
    else:
        return f"{u} (☠️ UV cực đoan)"

def _format_uv_max(val: Any) -> str:
    u = _to_float(val)
    if u is None:
        return "0 (không có số liệu)"
    u = _round1(u)
    if u < 3:
        return f"{u} (🙂 UV tối đa thấp)"
    elif u < 6:
        return f"{u} (ℹ️ UV tối đa trung bình)"
    elif u < 8:
        return f"{u} (⚠️ UV tối đa cao)"
    elif u < 11:
        return f"{u} (🚨 UV tối đa rất cao)"
    else:
        return f"{u} (☠️ UV tối đa cực đoan)"

# -------------------------------
# Hàm tổng hợp cho bulletin
# -------------------------------
def build_solar_uv_summary_v3(
    unified: Dict[str, Any],
    region: str = "north",
    now: Optional[datetime.datetime] = None
) -> Dict[str, Any]:
    # Chuẩn hóa thời điểm hiện tại
    now = now or datetime.datetime.now()

    # Lấy dữ liệu đầu vào
    solar_now = unified.get("solar")
    avg_solar = unified.get("avg_solar")
    solar_sum_day = unified.get("solar_sum_day")

    uv_now = unified.get("uv_now")
    avg_uv = unified.get("avg_uv")
    uv_max_day = unified.get("uv_max_day")

    precipitation = unified.get("precipitation_now") or unified.get("precipitation_day")
    cloudcover = unified.get("cloudcover_now") or unified.get("cloudcover_mean")

    # Ban đêm: không có bức xạ/UV → luôn gán 0
    if _is_night(now):
        lines: List[str] = [
            "🔆 Bức xạ mặt trời: 0 W/m² (🌙 Ban đêm, không có bức xạ)",
            "☀️ UV: 0 (🌙 Ban đêm, UV = 0)"
        ]
        return {
            "values": {
                "solar_now": 0,
                "avg_solar": 0,
                "solar_sum_day": 0,
                "uv_now": 0,
                "avg_uv": 0,
                "uv_max_day": 0,
                "solar_level": "🌙 Ban đêm, không có bức xạ",
                "uv_level_now": "🌙 Ban đêm, UV = 0",
                "uv_level_avg": "🌙 Ban đêm, UV = 0",
                "uv_level_max": "🌙 Ban đêm, UV = 0",
            },
            "lines": lines,
        }

    # Phân loại mức độ (fallback solar hiện tại -> solar trung bình)
    solar_level = classify_solar(
        solar_now, region=region, cloudcover=cloudcover, now=now
    ) or classify_solar(
        avg_solar, region=region, cloudcover=cloudcover, now=now
    )

    uv_level_now = classify_uv(
        uv_now, precipitation=precipitation, cloudcover=cloudcover, now=now
    ) if uv_now is not None else None

    uv_level_avg = classify_uv(
        avg_uv, precipitation=precipitation, cloudcover=cloudcover, now=now
    ) if avg_uv is not None else None

    uv_level_max = classify_uv(
        uv_max_day, precipitation=precipitation, cloudcover=cloudcover, now=now
    ) if uv_max_day is not None else None

    # Định dạng gọn
    def fmt(v, unit=""):
        val = _to_float(v)
        return "0" if val is None else f"{_round1(val)}{unit}"

    # Hiển thị ban ngày
    lines: List[str] = [
        f"🔆 Bức xạ mặt trời hiện tại: {fmt(solar_now, ' W/m²')} ({solar_level or '—'})",
        f"🔆 Bức xạ mặt trời trung bình ngày: {fmt(avg_solar, ' W/m²') if avg_solar is not None else '0 W/m²'}",
        f"🔆 Năng lượng bức xạ tích lũy trong ngày: {_format_solar_sum(solar_sum_day) if solar_sum_day is not None else '0 Wh/m²'}",
    ]

    # UV hiện tại: chỉ hiển thị khi có dữ liệu
    if uv_now is not None:
        lines.append(f"☀️ UV hiện tại: {fmt(uv_now)} ({uv_level_now or '—'})")

    # UV trung bình: chỉ hiển thị khi có dữ liệu
    if avg_uv is not None:
        lines.append(f"☀️ UV trung bình ngày: {fmt(avg_uv)} ({uv_level_avg or '—'})")

    # UV tối đa: luôn hiển thị
    lines.append(
        f"☀️ UV tối đa trong ngày: {fmt(uv_max_day) if uv_max_day is not None else '0'} ({uv_level_max or '—'})"
    )

    return {
        "values": {
            "solar_now": _round1(_to_float(solar_now)) if solar_now is not None else 0,
            "avg_solar": _round1(_to_float(avg_solar)) if avg_solar is not None else 0,
            "solar_sum_day": _round1(_to_float(solar_sum_day)) if solar_sum_day is not None else 0,
            "uv_now": _round1(_to_float(uv_now)) if uv_now is not None else None,  # giữ None nếu không có
            "avg_uv": _round1(_to_float(avg_uv)) if avg_uv is not None else None,  # giữ None nếu không có
            "uv_max_day": _round1(_to_float(uv_max_day)) if uv_max_day is not None else 0,
            "solar_level": solar_level if solar_level is not None else "—",
            "uv_level_now": uv_level_now if uv_level_now is not None else None,  # giữ None nếu không có
            "uv_level_avg": uv_level_avg if uv_level_avg is not None else None,  # giữ None nếu không có
            "uv_level_max": uv_level_max if uv_level_max is not None else "—",
        },
        "lines": lines,
    }