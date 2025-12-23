# services/summary.py
import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List

def build_summary(
    current_block: str,
    overview_block: str,
    current_values: Dict[str, Any],
    overview_values: Dict[str, Any] = None,
    insights: List[str] = None,
    alerts: List[str] = None
) -> Dict[str, Any]:
    overview_values = overview_values or {}
    summary_lines: List[str] = []

    def ov(key, default="—"):
        return overview_values.get(key, default)
    def cv(key, default="—"):
        return current_values.get(key, default)

    # 🕒 Thời gian quan trắc (hiển thị tiếng Việt)
    weekday_map = {
        0: "Thứ Hai", 1: "Thứ Ba", 2: "Thứ Tư",
        3: "Thứ Năm", 4: "Thứ Sáu", 5: "Thứ Bảy", 6: "Chủ Nhật",
    }
    now_local = datetime.datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
    weekday_vi = weekday_map[now_local.weekday()]
    timestamp = now_local.strftime(f"%H:%M • {weekday_vi}, %d/%m/%Y")

    # 👁️ Nhóm mở đầu khối kết luận: kết luận + thời gian + nguồn (liền nhau)
    status_text = current_values.get("status_text") or overview_values.get("status_text") or "—"
    summary_lines.append(f"📋 Kết luận: {status_text}")
    summary_lines.append(f"🕒 Thời gian quan trắc: {timestamp}")
    summary_lines.append(f"📄 Nguồn dữ liệu: Open_MeteoAPI")
    summary_lines.append("")
    
    # 🌡️ Nhiệt độ
    summary_lines.append(
        f"🌡️ Nhiệt độ hiện tại: {cv('temperature_now')}°C "
        f"(trung bình ngày: {ov('avg_temperature_day')}°C)"
    )
    summary_lines.append(
        f"🌡️ Dao động ngày: {ov('temperature_2m_min_day')}°C – {ov('temperature_2m_max_day')}°C"
    )

    # 🌧️ Mưa
    summary_lines.append(
        f"🌧️ Lượng mưa hiện tại: {cv('rain_now')} mm/h, Tổng ngày: {ov('precipitation_sum_day')} mm"
    )
    summary_lines.append(
        f"🌦️ Lượng mưa trung bình ngày: {ov('avg_precipitation_day')} mm/h"
    )

    # 💨 Gió
    summary_lines.append(
        f"💨 Gió hiện tại: {cv('wind_speed_now')} m/s (giật {cv('gust_now')} m/s), "
        f"Trung bình ngày: {ov('avg_wind_speed_day')} m/s, "
        f"Cực đại ngày: {ov('wind_speed_max')} m/s"
    )
    summary_lines.append(
        f"💨 Gió giật cực đại ngày: {ov('wind_gusts_max')} m/s"
    )

    # ☁️ Mây
    summary_lines.append(
        f"☁️ Mây hiện tại: {cv('cloudcover_now')}%, Trung bình ngày: {ov('cloudcover_mean')}%"
    )

    # 🌫️ Điểm sương
    summary_lines.append(
        f"🌫️ Điểm sương hiện tại: {cv('dewpoint_now')}°C, Trung bình ngày: {ov('dewpoint_mean')}°C"
    )

    # 👀 Tầm nhìn
    summary_lines.append(
        f"👀 Tầm nhìn hiện tại: {cv('visibility_now_km')} km"
    )

    # 💧 Độ ẩm
    summary_lines.append(
        f"💧 Độ ẩm hiện tại: {cv('humidity_now')}%, Trung bình ngày: {ov('humidity_day')}%"
    )

    # ⚖️ Áp suất
    summary_lines.append(
        f"⚖️ Áp suất hiện tại: {cv('pressure_now')} hPa, Trung bình ngày: {ov('pressure_day')} hPa"
    )

    # 🔆 Bức xạ mặt trời
    summary_lines.append(
        f"🔆 Bức xạ hiện tại: {cv('solar_now')} W/m², Tổng ngày tích lũy: {ov('solar_sum_day')}"
    )

    # ☀️ UV
    summary_lines.append(
        f"☀️ UV hiện tại: {cv('uv_now')}, Tối đa ngày: {ov('uv_max_day')}"
    )

    # 🌅 Mặt trời mọc/lặn (chuẩn hóa định dạng Việt Nam)
    sunrise_raw = ov("sunrise")
    sunset_raw = ov("sunset")

    def format_dt(dt_str: str) -> str:
        try:
            dt = datetime.datetime.fromisoformat(dt_str)
            return dt.strftime("%H:%M, %d/%m/%Y")
        except Exception:
            return dt_str

    sunrise_fmt = format_dt(sunrise_raw)
    sunset_fmt = format_dt(sunset_raw)

    summary_lines.append(f"🌅 Mặt trời mọc: {sunrise_fmt}, 🌇 Mặt trời lặn: {sunset_fmt}")

    # 👉 Chèn dòng trống sau nhóm số liệu gốc
    summary_lines.append("")

    # 📌 Nhận định nổi bật
    if insights:
        summary_lines.append("📌 NHẬN ĐỊNH NỔI BẬT")
        for ins in insights:
            summary_lines.append(f"🔎 {ins}")
        summary_lines.append("")

    # ⚠️ Cảnh báo quan trọng
    if alerts:
        summary_lines.append("⚠️ CẢNH BÁO QUAN TRỌNG")
        for al in alerts:
            summary_lines.append(f"⚠️ {al}")

    if not summary_lines:
        summary_lines.append("✅ Không có yếu tố thời tiết đáng chú ý.")

    summary_block = "\n".join(summary_lines)

    text = (
        "# 📰 KẾT LUẬN BẢN TIN\n\n"
        + summary_block
    )

    return {
        "text": text,
        "summary_block": summary_block,
    }