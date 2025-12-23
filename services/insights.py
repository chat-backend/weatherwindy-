# services/insights.py
from typing import Dict, Any, List

def interpret_temperature(temp: float = None, feels: float = None,
                          tmin: float = None, tmax: float = None,
                          avg_temp: float = None,
                          avg_temp_hour: float = None) -> List[str]:
    insights = []
    if temp is not None:
        if temp >= 45:
            insights.append("🔥 Nhiệt độ cực cao (≥45°C), nguy cơ sốc nhiệt nghiêm trọng.")
        elif 40 <= temp < 45:
            insights.append("🔥 Nhiệt độ rất cao (40–44°C), dễ gây oi bức.")
        elif 35 <= temp < 40:
            insights.append("🔥 Nắng nóng mạnh (35–39°C).")
        elif 30 <= temp < 35:
            insights.append("🔥 Thời tiết nóng (30–34°C).")
        elif 25 <= temp < 30:
            insights.append("🙂 Nhiệt độ ôn hòa, khá dễ chịu.")
        elif 20 <= temp < 25:
            insights.append("❄️ Thời tiết hơi lạnh (20–24°C).")
        elif 15 <= temp < 20:
            insights.append("❄️ Trời lạnh (15–19°C), cần giữ ấm.")
        else:  # <15
            insights.append("❄️ Rét đậm (<15°C), nguy cơ hạ thân nhiệt.")

    # Cảm giác thực tế
    if feels is not None and temp is not None:
        diff = feels - temp
        if abs(diff) >= 3:
            sign = "nóng hơn" if diff > 0 else "lạnh hơn"
            insights.append(f"🤔 Cảm giác thực tế {sign} {abs(diff):.1f}°C so với nhiệt độ đo được.")
        else:
            insights.append("🙂 Cảm giác thực tế tương đồng với nhiệt độ đo được.")

    # Biên độ nhiệt trong ngày
    if tmin is not None and tmax is not None:
        dr = tmax - tmin
        if dr >= 10:
            insights.append("📈 Biên độ nhiệt trong ngày lớn, thời tiết thay đổi rõ rệt.")
        else:
            insights.append("📉 Biên độ nhiệt trong ngày nhỏ, biến thiên nhẹ.")
        if avg_temp is None:
            avg_temp = (tmin + tmax) / 2

    # Trung bình ngày
    if avg_temp is not None:
        insights.append(f"🌡️ Nhiệt độ trung bình ngày khoảng {avg_temp:.1f}°C.")

    # Lệch theo giờ
    if temp is not None and avg_temp_hour is not None and avg_temp_hour > 0:
        ratio = temp / avg_temp_hour
        if ratio >= 1.3:
            insights.append("⚠️ Nhiệt độ hiện tại cao hơn đáng kể so với trung bình giờ.")
        elif ratio <= 0.7:
            insights.append("⚠️ Nhiệt độ hiện tại thấp hơn đáng kể so với trung bình giờ.")
        else:
            insights.append("ℹ️ Nhiệt độ gần mức trung bình giờ.")

    return insights

# -------------------------------
# Nhận định mưa
# -------------------------------
# -------------------------------
# Nhận định mưa (bỏ trung bình ngày)
# -------------------------------
def interpret_rain(
    rain: float = None,
    rain_total_day: float = None,
    avg_rain: float = None
) -> List[str]:
    insights = []
    if rain is not None:
        insights.append(f"🌧️ Lượng mưa hiện tại {rain:.1f} mm/h.")
    # Bỏ phần lượng mưa trung bình ngày
    if rain_total_day is not None:
        insights.append(f"🌦️ Tổng lượng mưa ngày {rain_total_day:.1f} mm.")
    return insights

# -------------------------------
# Nhận định xác suất mưa
# -------------------------------
def interpret_rain_probability(rain_prob: float = None) -> List[str]:
    insights = []
    if rain_prob is not None:
        if rain_prob >= 70:
            insights.append(f"⚠️ Xác suất mưa cao ({rain_prob:.0f}%), nên chuẩn bị áo mưa.")
        elif rain_prob >= 40:
            insights.append(f"ℹ️ Khả năng có mưa ({rain_prob:.0f}%), theo dõi radar mưa.")
        else:
            insights.append(f"🙂 Xác suất mưa thấp ({rain_prob:.0f}%).")
    return insights

# -------------------------------
# Nhận định gió
# -------------------------------
def interpret_wind(wspd: float = None, gust: float = None, avg_wspd: float = None) -> List[str]:
    insights = []
    if wspd is not None:
        insights.append(f"💨 Gió hiện tại {wspd:.1f} m/s.")
        if wspd >= 50.5:
            insights.append("⚠️ Gió rất mạnh (≥50.5 m/s), cực kỳ nguy hiểm.")
        elif wspd >= 45.7:
            insights.append("⚠️ Bão mạnh (≥45.7 m/s).")
        elif wspd >= 40.5:
            insights.append("⚠️ Có dấu hiệu bão (≥40.5 m/s).")
        elif wspd >= 35.2:
            insights.append("⚠️ Gió rất mạnh (≥35.2 m/s).")
        elif wspd >= 30.8:
            insights.append("⚠️ Gió mạnh (≥30.8 m/s).")
    if gust is not None:
        insights.append(f"🌬️ Gió giật {gust:.1f} m/s.")
    if avg_wspd is not None:
        insights.append(f"🍃 Gió trung bình ngày {avg_wspd:.1f} m/s.")
    return insights

# -------------------------------
# Nhận định hướng gió (8 hướng)
# -------------------------------
def interpret_wind_direction(dir: float = None) -> List[str]:
    insights = []
    if dir is not None:
        insights.append(f"↔️ Hướng gió hiện tại {dir:.1f}°.")
        # Chia thành 8 hướng, mỗi hướng 45°
        if 22.5 <= dir < 67.5:
            insights.append("🌬️ Gió Đông Bắc.")
        elif 67.5 <= dir < 112.5:
            insights.append("🌬️ Gió Đông.")
        elif 112.5 <= dir < 157.5:
            insights.append("🌬️ Gió Đông Nam.")
        elif 157.5 <= dir < 202.5:
            insights.append("🌬️ Gió Nam.")
        elif 202.5 <= dir < 247.5:
            insights.append("🌬️ Gió Tây Nam.")
        elif 247.5 <= dir < 292.5:
            insights.append("🌬️ Gió Tây.")
        elif 292.5 <= dir < 337.5:
            insights.append("🌬️ Gió Tây Bắc.")
        else:
            # Bao gồm cả 337.5–360 và 0–22.5
            insights.append("🌬️ Gió Bắc.")
    return insights

# -------------------------------
# Nhận định mây (chuẩn hóa ngưỡng)
# -------------------------------
def interpret_cloudcover(cloud: float = None, avg_cloud: float = None) -> List[str]:
    insights = []
    if cloud is not None:
        insights.append(f"☁️ Độ che phủ mây hiện tại {cloud:.0f}%.")
        if cloud >= 95:
            insights.append("☁️ Trời u ám, mây dày đặc.")
        elif 85 <= cloud < 95:
            insights.append("☁️ Nhiều mây, ánh sáng mặt trời hạn chế.")
        elif 50 <= cloud < 85:
            insights.append("⛅ Mây vừa phải, trời khá thoáng.")
        else:  # <50
            insights.append("☀️ Trời quang đãng, hầu như không có mây.")
    if avg_cloud is not None:
        insights.append(f"☁️ Độ che phủ mây trung bình ngày {avg_cloud:.0f}%.")
    return insights

# -------------------------------
# Nhận định điểm sương
# -------------------------------
def interpret_dewpoint(dew: float = None, avg_dew: float = None) -> List[str]:
    insights = []
    if dew is not None:
        insights.append(f"🌡️ Điểm sương hiện tại {dew:.1f}°C.")
        if dew >= 24:
            insights.append("🔥 Điểm sương rất cao (≥24°C), không khí ngột ngạt, oi bức.")
        elif 20 <= dew < 24:
            insights.append("🌫️ Điểm sương cao (20–23°C), không khí ẩm, dễ đổ mồ hôi.")
        elif 15 <= dew < 20:
            insights.append("🙂 Điểm sương trung bình (15–19°C), không khí dễ chịu.")
        elif 10 <= dew < 15:
            insights.append("🍃 Điểm sương thấp (10–14°C), không khí khô ráo.")
        else:  # <10
            insights.append("❄️ Điểm sương rất thấp (<10°C), không khí khô hanh.")
    if avg_dew is not None:
        insights.append(f"🌡️ Điểm sương trung bình ngày {avg_dew:.1f}°C.")
    return insights

# -------------------------------
# Nhận định tầm nhìn
# -------------------------------
def interpret_visibility(vis: float = None) -> List[str]:
    insights = []
    if vis is not None:
        # Nếu dữ liệu gốc là mét, chuyển sang km
        if vis > 100:  # giả định >100 nghĩa là đang ở đơn vị mét
            vis_km = vis / 1000.0
        else:
            vis_km = vis

        insights.append(f"👁️ Tầm nhìn hiện tại {vis_km:.1f} km.")
        if vis_km < 1:
            insights.append("⚠️ Tầm nhìn rất hạn chế (<1 km), nguy hiểm khi di chuyển.")
        elif vis_km < 5:
            insights.append("⚠️ Tầm nhìn kém (<5 km), cần thận trọng khi lái xe.")
        elif vis_km < 10:
            insights.append("ℹ️ Tầm nhìn trung bình.")
        else:
            insights.append("🙂 Tầm nhìn xa, điều kiện thuận lợi.")
    return insights

# -------------------------------
# Nhận định độ ẩm
# -------------------------------
def interpret_humidity(rh: float = None, avg_rh: float = None) -> List[str]:
    insights = []
    if rh is not None:
        insights.append(f"💧 Độ ẩm hiện tại {rh:.0f}%.")
        if rh >= 95:
            insights.append("⚠️ Độ ẩm rất cao (≥95%), dễ nồm ẩm, không khí bí, đồ đạc ẩm mốc.")
        elif 85 <= rh < 95:
            insights.append("⚠️ Độ ẩm cao (85–94%), nguy cơ nồm ẩm.")
        elif 60 <= rh < 85:
            insights.append("ℹ️ Độ ẩm trung bình (60–84%), khá dễ chịu.")
        else:  # <60
            insights.append("⚠️ Độ ẩm thấp (<60%), không khí khô hanh, dễ gây khô da và bệnh hô hấp.")
    if avg_rh is not None:
        insights.append(f"💧 Độ ẩm trung bình ngày {avg_rh:.0f}%.")
    return insights

# -------------------------------
# Nhận định áp suất
# -------------------------------
def interpret_pressure(pmsl: float = None, avg_pmsl: float = None) -> List[str]:
    insights = []
    if pmsl is not None:
        insights.append(f"⚖️ Áp suất hiện tại {pmsl:.0f} hPa.")
        if pmsl < 1000:
            insights.append("⚠️ Áp suất thấp, có thể ảnh hưởng sức khỏe người già và trẻ nhỏ.")
        elif pmsl > 1025:
            insights.append("⚠️ Áp suất cao bất thường, có thể gây khó chịu, đau đầu hoặc ảnh hưởng tuần hoàn.")
        else:
            insights.append("ℹ️ Áp suất trong khoảng bình thường (1000–1025 hPa).")
    if avg_pmsl is not None:
        insights.append(f"⚖️ Áp suất trung bình ngày {avg_pmsl:.0f} hPa.")
        if avg_pmsl < 1000:
            insights.append("⚠️ Áp suất trung bình thấp trong ngày, có thể ảnh hưởng sức khỏe.")
        elif avg_pmsl > 1025:
            insights.append("⚠️ Áp suất trung bình cao trong ngày, có thể ảnh hưởng sức khỏe tim mạch.")
        else:
            insights.append("ℹ️ Áp suất trung bình trong khoảng bình thường (1000–1025 hPa).")
    return insights

# -------------------------------
# Nhận định bức xạ mặt trời + UV (tách riêng uv_max_day)
# -------------------------------
def interpret_solar_uv(
    solar: float = None,
    avg_solar: float = None,
    uv: float = None,
    avg_uv: float = None,
    uv_max_day: float = None
) -> List[str]:
    insights = []

    # Bức xạ mặt trời
    if solar is not None:
        insights.append(f"🔆 Bức xạ mặt trời hiện tại {solar:.0f} W/m².")
        if solar >= 800:
            insights.append("⚠️ Bức xạ mặt trời cao, nguy cơ cháy nắng và ảnh hưởng sức khỏe.")
        elif solar >= 400:
            insights.append("ℹ️ Bức xạ mặt trời trung bình, có thể phơi nắng vừa phải.")
        else:
            insights.append("🔆 Bức xạ mặt trời yếu (<400 W/m²).")

    if avg_solar is not None:
        insights.append(f"🔆 Bức xạ mặt trời trung bình ngày {avg_solar:.0f} W/m².")
        if avg_solar >= 600:
            insights.append("⚠️ Bức xạ mặt trời trung bình cao trong ngày, cần hạn chế phơi nắng lâu.")

    # UV hiện tại
    if uv is not None:
        insights.append(f"☀️ UV hiện tại {uv:.1f}.")
        if uv >= 11:
            insights.append("☀️ UV cực đoan (≥11), tránh nắng hoàn toàn.")
        elif uv >= 8:
            insights.append("🚨 UV rất cao (8–10), cần bảo vệ da và mắt.")
        elif uv >= 6:
            insights.append("⚠️ UV cao (6–7), nên dùng kem chống nắng.")
        elif uv >= 3:
            insights.append("ℹ️ UV trung bình (3–5), cần lưu ý khi ra ngoài lâu.")
        else:
            insights.append("🙂 UV thấp (0–2), an toàn khi ra ngoài.")

    # UV trung bình ngày
    if avg_uv is not None:
        insights.append(f"☀️ UV trung bình ngày {avg_uv:.1f}.")
        if avg_uv >= 8:
            insights.append("⚠️ UV trung bình rất cao trong ngày, cần bảo vệ da khi hoạt động ngoài trời.")
        elif avg_uv >= 6:
            insights.append("⚠️ UV trung bình cao trong ngày, nên dùng kem chống nắng.")

    # UV tối đa trong ngày
    if uv_max_day is not None:
        insights.append(f"☀️ UV tối đa trong ngày {uv_max_day:.1f}.")
        if uv_max_day >= 11:
            insights.append("☀️ UV tối đa cực đoan trong ngày, nguy cơ cháy nắng mạnh.")
        elif uv_max_day >= 8:
            insights.append("🚨 UV tối đa rất cao trong ngày, cần bảo vệ da và mắt.")
        elif uv_max_day >= 6:
            insights.append("⚠️ UV tối đa cao trong ngày, nên dùng kem chống nắng.")
        elif uv_max_day >= 3:
            insights.append("ℹ️ UV tối đa trung bình trong ngày, cần lưu ý khi ra ngoài lâu.")
        else:
            insights.append("🙂 UV tối đa thấp trong ngày, khá an toàn.")

    return insights 


# -------------------------------
# Hàm tổng hợp cho tất cả (tối ưu)
# -------------------------------
def generate_all_insights(unified: Dict[str, Any]) -> List[str]:
    insights: List[str] = []

    # Nhiệt độ
    insights.extend(interpret_temperature(
        temp=unified.get("temperature_now") or unified.get("temperature"),
        feels=unified.get("apparent_temperature_now") or unified.get("apparent_temperature"),
        tmin=unified.get("temperature_min"),
        tmax=unified.get("temperature_max"),
        avg_temp=unified.get("temperature_day") or unified.get("avg_temperature_day") or unified.get("avg_temperature"),
        avg_temp_hour=unified.get("temperature_hourly") or unified.get("avg_temperature_hourly")
    ))

    # Mưa
    insights.extend(interpret_rain(
        rain=unified.get("precipitation_now") or unified.get("precipitation") or unified.get("rain_now") or unified.get("rain"),
        rain_total_day=unified.get("precipitation_sum_day") or unified.get("precipitation_sum") or unified.get("rain_total_day"),
        avg_rain=unified.get("avg_precipitation_day") or unified.get("precipitation_hourly") or unified.get("avg_precipitation") or unified.get("avg_rain")
    ))

    # Xác suất mưa
    insights.extend(interpret_rain_probability(
        rain_prob=unified.get("precipitation_probability_now") or unified.get("precipitation_probability") or unified.get("rain_prob")
    ))
    insights.extend(interpret_rain_probability(
        rain_prob=unified.get("precipitation_probability_day") or unified.get("rain_prob_day")
    ))

    # Gió
    insights.extend(interpret_wind(
        wspd=unified.get("wind_speed_now") or unified.get("wind_speed") or unified.get("wspd"),
        gust=unified.get("gust_now") or unified.get("gust"),
        avg_wspd=unified.get("wind_speed_hourly") or unified.get("avg_wind_speed_day") or unified.get("avg_wind_speed")
    ))

    # Hướng gió
    insights.extend(interpret_wind_direction(
        dir=unified.get("wind_direction_now") or unified.get("wind_direction") or unified.get("wind_dir")
    ))

    # Mây
    insights.extend(interpret_cloudcover(
        cloud=unified.get("cloudcover_now") or unified.get("cloudcover"),
        avg_cloud=unified.get("cloudcover_mean") or unified.get("avg_cloudcover_day")
    ))

    # Điểm sương
    insights.extend(interpret_dewpoint(
        dew=unified.get("dewpoint_now") or unified.get("dewpoint"),
        avg_dew=unified.get("dewpoint_2m_mean") or unified.get("dewpoint_mean") or unified.get("avg_dewpoint_day")
    ))

    # Tầm nhìn
    insights.extend(interpret_visibility(
        vis=unified.get("visibility_now") or unified.get("visibility")
    ))

    # Độ ẩm
    insights.extend(interpret_humidity(
        rh=unified.get("humidity_now") or unified.get("humidity"),
        avg_rh=unified.get("humidity_day") or unified.get("avg_humidity")
    ))

    # Áp suất
    insights.extend(interpret_pressure(
        pmsl=unified.get("pressure_now") or unified.get("pressure"),
        avg_pmsl=unified.get("pressure_day") or unified.get("avg_pressure")
    ))

    # Bức xạ mặt trời + UV
    insights.extend(interpret_solar_uv(
        solar=unified.get("solar_radiation_now"),
        avg_solar=unified.get("solar_radiation_sum_day") or unified.get("avg_solar"),
        uv=unified.get("uv_index_now"),
        avg_uv=unified.get("uv_index_hourly"),
        uv_max_day=unified.get("uv_index_max_day")
    ))

    return insights


# -------------------------------
# Nhận định riêng cho khối hiện tại (chuẩn hóa, có ghi chú)
# -------------------------------
def generate_current_insights(values: Dict[str, Any]) -> List[str]:
    insights = ["⏱️ NHẬN ĐỊNH TÌNH HÌNH HIỆN TẠI:"]

    # Nhiệt độ hiện tại
    insights.extend(interpret_temperature(
        temp=values.get("temperature"),
        feels=values.get("apparent_temperature"),
        avg_temp_hour=values.get("avg_temperature_hourly")
    ))

    # Lượng mưa hiện tại
    insights.extend(interpret_rain(
        rain=values.get("rain")
    ))

    # Xác suất mưa hiện tại
    insights.extend(interpret_rain_probability(
        rain_prob=values.get("rain_prob")
    ))

    # Gió hiện tại
    insights.extend(interpret_wind(
        wspd=values.get("wspd"),
        gust=values.get("gust")
    ))

    insights.extend(interpret_wind_direction(
        dir=values.get("wind_dir")
    ))

    # Mây
    insights.extend(interpret_cloudcover(
        cloud=values.get("cloudcover")
    ))

    # Điểm sương
    insights.extend(interpret_dewpoint(
        dew=values.get("dewpoint")
    ))

    # Tầm nhìn
    insights.extend(interpret_visibility(
        vis=values.get("visibility")
    ))

    # Độ ẩm
    insights.extend(interpret_humidity(
        rh=values.get("humidity")
    ))

    # Áp suất
    insights.extend(interpret_pressure(
        pmsl=values.get("pressure")
    ))

    # Bức xạ mặt trời + UV
    insights.extend(interpret_solar_uv(
        solar=values.get("solar"),
        uv=values.get("uv_now"),
        uv_max_day=values.get("uv_max_day")
    ))

    return insights if len(insights) > 1 else [
        "⏱️ NHẬN ĐỊNH TÌNH HÌNH HIỆN TẠI:",
        "ℹ️ Không có nhận định đặc biệt cho tình hình hiện tại."
    ]


# -------------------------------
# Nhận định riêng cho khối tổng quan (chuẩn hóa)
# -------------------------------
def generate_overview_insights(values: Dict[str, Any]) -> List[str]:
    insights = ["📅 NHẬN ĐỊNH TỔNG QUAN TRONG NGÀY:"]

    # Nhiệt độ tổng quan
    insights.extend(interpret_temperature(
        tmin=values.get("tmin"),
        tmax=values.get("tmax"),
        avg_temp=values.get("avg_temperature")
    ))

    # Gió trung bình ngày
    insights.extend(interpret_wind(
        avg_wspd=values.get("avg_wind_speed")
    ))

    # Xác suất mưa ngày
    insights.extend(interpret_rain_probability(
        rain_prob=values.get("rain_prob_day")
    ))

    # Mưa tổng quan
    insights.extend(interpret_rain(
        rain_total_day=values.get("rain_total_day"),
        avg_rain=values.get("avg_rain")
    ))

    # Độ ẩm trung bình ngày
    insights.extend(interpret_humidity(
        avg_rh=values.get("avg_humidity")
    ))

    # Mây trung bình ngày
    insights.extend(interpret_cloudcover(
        avg_cloud=values.get("cloudcover_mean")
    ))

    # Điểm sương trung bình ngày
    insights.extend(interpret_dewpoint(
        avg_dew=values.get("dewpoint_mean")
    ))

    # Tầm nhìn tổng quan
    insights.extend(interpret_visibility(
        vis=values.get("visibility")
    ))

    # Áp suất trung bình ngày
    insights.extend(interpret_pressure(
        avg_pmsl=values.get("avg_pressure")
    ))

    # Bức xạ + UV
    insights.extend(interpret_solar_uv(
        avg_solar=values.get("avg_solar"),
        avg_uv=values.get("avg_uv"),
        uv_max_day=values.get("uv_max_day")
    ))

    return insights if len(insights) > 1 else [
        "📅 NHẬN ĐỊNH TỔNG QUAN TRONG NGÀY:",
        "ℹ️ Không có nhận định đặc biệt cho tổng quan trong ngày."
    ]