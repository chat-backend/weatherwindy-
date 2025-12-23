# services/wind.py
from typing import Dict, Any, List, Optional

def _to_float(val: Any) -> Optional[float]:
    try:
        if val is None:
            return None
        return float(val)
    except Exception:
        return None

def _round1(val: Optional[float]) -> Optional[float]:
    return None if val is None else round(val, 1)

def fmt(val: Any, unit: str = " m/s") -> str:
    v = _to_float(val)
    if v is None:
        return "—"
    return f"{_round1(v)}{unit}"

def wind_direction_to_text(deg: Any) -> str:
    d = _to_float(deg)
    if d is None:
        return "—"
    dirs = ["Bắc", "Đông Bắc", "Đông", "Đông Nam", "Nam", "Tây Nam", "Tây", "Tây Bắc"]
    ix = int((d + 22.5) % 360 / 45)
    return dirs[ix]

# -------------------------------
# Các hàm tính toán gió
# -------------------------------
def compute_effective_wind(wspd: Any, gust: Any) -> Optional[float]:
    w = _to_float(wspd)
    g = _to_float(gust)
    if w is None:
        return None
    if g is None:
        g_eff = w
    else:
        g_eff = min(g, w * 1.5)
    eff = 0.7 * w + 0.3 * g_eff
    return _round1(eff)

def classify_wind_level(wspd: Any, gust: Any = None, region: str = "north") -> Optional[str]:
    eff = compute_effective_wind(wspd, gust)
    if eff is None:
        return None
    if region == "north":
        # Miền Bắc: quen gió mùa, ngưỡng cảm nhận cao hơn
        if eff >= 20: return "💨 Gió rất mạnh, nguy hiểm khi di chuyển ngoài trời."
        if eff >= 12: return "💨 Gió mạnh, có thể gây khó khăn khi đi lại."
        if eff >= 6:  return "🍃 Gió vừa, cảm nhận rõ rệt."
        if eff > 0:   return "🍃 Gió nhẹ, thoáng mát."
        return "🙂 Lặng gió."
    else:
        # Miền Trung/Nam: ít gió mùa, ngưỡng cảm nhận thấp hơn
        if eff >= 15: return "💨 Gió rất mạnh, nguy hiểm khi di chuyển ngoài trời."
        if eff >= 8:  return "💨 Gió mạnh, có thể gây khó khăn khi đi lại."
        if eff >= 4:  return "🍃 Gió vừa, cảm nhận rõ rệt."
        if eff > 0:   return "🍃 Gió nhẹ, thoáng mát."
        return "🙂 Lặng gió."

def classify_wind_beaufort(wspd: Any, avg_wspd: Any = None, gust: Any = None) -> Optional[int]:
    sustained = _to_float(avg_wspd) if _to_float(avg_wspd) is not None else _to_float(wspd)
    if sustained is None:
        return None
    w = sustained
    if w < 0.3: return 0
    if w < 1.6: return 1
    if w < 3.4: return 2
    if w < 5.5: return 3
    if w < 8.0: return 4
    if w < 10.8: return 5
    if w < 13.9: return 6
    if w < 17.2: return 7
    if w < 20.8: return 8
    if w < 24.5: return 9
    if w < 28.5: return 10
    if w < 32.7: return 11
    return 12

def interpret_gust(gust: Any, wspd: Any, region: str = "north") -> Optional[str]:
    g, w = _to_float(gust), _to_float(wspd)
    if g is None or w is None:
        return None
    if region == "north":
        if g >= max(6.0, w * 1.6):
            return "⚠️ Gió giật mạnh hơn nhiều so với gió trung bình."
        if g >= w * 1.3:
            return "ℹ️ Có gió giật, cần chú ý."
        return "🙂 Gió giật không đáng kể."
    else:
        if g >= max(5.0, w * 1.4):
            return "⚠️ Gió giật mạnh hơn nhiều so với gió trung bình."
        if g >= w * 1.2:
            return "ℹ️ Có gió giật, cần chú ý."
        return "🙂 Gió giật không đáng kể."

def adjust_feels_by_wind(temp: Any, feels: Any, wspd: Any, gust: Any = None, region: str = "north") -> Optional[float]:
    t = _to_float(temp)
    f = _to_float(feels)
    eff = compute_effective_wind(wspd, gust)
    if t is None or f is None or eff is None:
        return None
    reduction = eff / 4.0
    max_drop = 6.0 if region == "north" else 5.0
    if t <= 20 and region != "north":
        max_drop = 7.0
    reduction = min(reduction, max_drop)
    adjusted = f - reduction
    return _round1(adjusted)

# -------------------------------
# Phiên bản đồng bộ với unified helpers
# -------------------------------
def build_wind_summary(unified: Dict[str, Any], wind_unit: str = " m/s", region: str = "north") -> Dict[str, Any]:
    wspd   = unified.get("wind_speed_now")
    gust   = unified.get("gust_now")
    avg_wspd = unified.get("avg_wind_speed_day")
    temp   = unified.get("temperature_now")
    feels  = unified.get("apparent_temperature_now")
    wind_dir = unified.get("wind_direction_now") or unified.get("wind_direction_day")

    # Phân loại theo vùng miền
    level_text = classify_wind_level(wspd, gust, region=region)
    gust_text  = interpret_gust(gust, wspd, region=region)
    wind_level = classify_wind_beaufort(wspd, avg_wspd, gust)

    # Gió hiệu dụng và cảm giác điều chỉnh
    eff_wind = compute_effective_wind(wspd, gust)
    feels_adj_by_wind = adjust_feels_by_wind(temp, feels, wspd, gust, region=region)

    # Chuỗi hiển thị
    lines: List[str] = [
        f"🍃 Gió hiện tại: {fmt(wspd, wind_unit)}",
        f"💨 Gió giật: {fmt(gust, wind_unit)}",
        f"🌬️ Gió trung bình ngày: {fmt(avg_wspd, wind_unit)}",
        f"🌀 Cấp gió Beaufort (theo gió duy trì): {wind_level if wind_level is not None else '—'}",
    ]
    if wind_dir is not None:
        lines.append(f"↔️ Hướng gió: {fmt(wind_dir, '°')} ({wind_direction_to_text(wind_dir)})")

    if level_text:
        lines.append(level_text)
    if gust_text:
        lines.append(gust_text)
    if eff_wind is not None:
        lines.append(f"🍃 Gió hiệu dụng (cảm nhận): {eff_wind} {wind_unit.strip()}")

    return {
        "values": {
            "wind_speed_now": _round1(_to_float(wspd)),
            "gust_now": _round1(_to_float(gust)),
            "avg_wind_speed_day": _round1(_to_float(avg_wspd)),
            "effective_wind": eff_wind,
            "wind_level_desc": level_text,
            "wind_level": wind_level,
            "feels_adjusted_by_wind": feels_adj_by_wind,
            "wind_direction": _round1(_to_float(wind_dir)),
            "wind_direction_text": wind_direction_to_text(wind_dir) if wind_dir is not None else None,
        },
        "lines": lines,
    }

def build_wind_block(unified: Dict[str, Any], wind_unit: str = " m/s", region: str = "north") -> str:
    summary = build_wind_summary(unified, wind_unit, region=region)
    block_text = "\n".join(summary["lines"])
    return block_text