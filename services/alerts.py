# services/alerts.py
from typing import Dict, Any, List

def generate_temperature_alerts(
    temp: float = None, feels: float = None,
    tmin: float = None, tmax: float = None,
    avg_temp: float = None, avg_temp_hour: float = None
) -> List[str]:
    alerts = []
    if temp is not None:
        # Nắng nóng
        if temp >= 45:
            alerts.append("⚠️ Nhiệt độ cực cao (≥45°C): nguy cơ sốc nhiệt nghiêm trọng, cần hạn chế ra ngoài.")
        elif temp >= 40:
            alerts.append("⚠️ Nắng nóng gay gắt (≥40°C), oi bức, dễ kiệt sức.")
        elif temp >= 35:
            alerts.append("⚠️ Thời tiết nóng (≥35°C), gây khó chịu, cần hạn chế ra ngoài.")

        # Lạnh
        if temp <= 7:
            alerts.append("⚠️ Rét buốt cực đoan (≤7°C): nguy cơ hạ thân nhiệt, cực kỳ nguy hiểm.")
        elif temp <= 10:
            alerts.append("⚠️ Rét hại (≤10°C): rất nguy hiểm, cần giữ ấm nghiêm ngặt.")
        elif temp <= 12:
            alerts.append("⚠️ Rét đậm (≤12°C): nguy cơ hạ thân nhiệt, cần giữ ấm cơ thể.")
        elif temp <= 15:
            alerts.append("⚠️ Rét nhẹ (≤15°C): dễ ảnh hưởng sức khỏe người già và trẻ nhỏ.")
        elif temp <= 18:
            alerts.append("⚠️ Trời lạnh (≤18°C): nhiều người cảm thấy run, cần mặc ấm.")

    # Dao động nhiệt độ lớn trong ngày
    if tmin is not None and tmax is not None and (tmax - tmin) >= 15:
        alerts.append("⚠️ Dao động nhiệt độ lớn trong ngày, dễ gây mệt mỏi.")

    # Lệch nhiều so với trung bình ngày
    if temp is not None and avg_temp is not None and abs(temp - avg_temp) >= 7:
        alerts.append("⚠️ Nhiệt độ hiện tại lệch nhiều so với trung bình ngày, thời tiết biến động bất thường.")

    # Cảm giác thực tế khác biệt
    if temp is not None and feels is not None and abs(feels - temp) >= 5:
        alerts.append("⚠️ Cảm giác thực tế khác biệt lớn so với nhiệt độ, dễ gây khó chịu.")

    # Lệch nhiều so với trung bình giờ
    if temp is not None and avg_temp_hour is not None and avg_temp_hour > 0:
        ratio_temp_hour = temp / avg_temp_hour
        if ratio_temp_hour >= 1.3:
            alerts.append("⚠️ Nhiệt độ hiện tại cao hơn nhiều so với trung bình giờ, thời tiết biến động bất thường.")
        elif ratio_temp_hour <= 0.7:
            alerts.append("⚠️ Nhiệt độ hiện tại thấp hơn nhiều so với trung bình giờ, nguy cơ lạnh đột ngột.")

    return alerts

# -------------------------------
# 2. 🌧️ Cảnh báo Mưa
# -------------------------------
def generate_rain_alerts(
    rain: float = None, rain_prob: float = None,
    avg_rain: float = None, avg_rain_hour: float = None,
    rain_total_day: float = None, gust: float = None,
    terrain: str = None
) -> List[str]:
    alerts = []
    if rain is not None and rain >= 20:
        alerts.append("⚠️ Mưa lớn, nguy cơ ngập úng và lũ quét.")
    if rain_prob is not None and rain_prob >= 70:
        alerts.append("⚠️ Xác suất mưa cao, nên chuẩn bị áo mưa/ô.")
    if rain is not None and avg_rain_hour and avg_rain_hour > 0:
        ratio_hour = rain / avg_rain_hour
        if ratio_hour >= 3:
            alerts.append("⚠️ Lượng mưa hiện tại gấp nhiều lần trung bình giờ, mưa dồn dập bất thường.")
        elif ratio_hour <= 0.3:
            alerts.append("⚠️ Lượng mưa hiện tại thấp hơn nhiều so với trung bình giờ, mưa phân bố không đều.")
    if avg_rain is not None and avg_rain >= 30:
        alerts.append("⚠️ Lượng mưa trung bình trong ngày cao, nguy cơ ngập úng kéo dài.")
    if rain_total_day is not None and rain_total_day >= 50:
        alerts.append("⚠️ Tổng lượng mưa trong ngày rất cao, nguy cơ ngập úng và lũ diện rộng.")
    if rain is not None and rain >= 50 and gust is not None and gust >= 20:
        alerts.append("⚠️ Mưa lớn kèm gió mạnh: nguy cơ bão, cần cảnh giác cao.")
    if terrain in ["mountain", "slope"] and rain is not None and avg_rain_hour and avg_rain_hour > 0:
        if rain / avg_rain_hour >= 3:
            alerts.append("⚠️ Mưa dồn dập theo giờ tại khu vực địa hình dốc/núi: nguy cơ lũ quét và sạt lở đất rất cao.")
    return alerts

# -------------------------------
# 3. 💨 Cảnh báo Gió (tốc độ + hướng)
# -------------------------------
def generate_wind_alerts(
    wspd: float = None, gust: float = None, avg_wspd: float = None, dir: float = None
) -> List[str]:
    alerts = []

    # --- Tốc độ gió hiện tại ---
    if wspd is not None:
        if wspd >= 41.5:
            alerts.append("⚠️ Gió cấp 14 (≥41.5 m/s): bão rất mạnh, cực kỳ nguy hiểm.")
        elif wspd >= 32.7:
            alerts.append("⚠️ Gió cấp 12 (≥32.7 m/s): bão mạnh, cần trú ẩn an toàn.")
        elif wspd >= 24.5:
            alerts.append("⚠️ Gió cấp 10 (≥24.5 m/s): có dấu hiệu bão, cần phòng tránh.")
        elif wspd >= 17.2:
            alerts.append("⚠️ Gió cấp 8 (≥17.2 m/s): gió rất mạnh, nguy hiểm cho tàu thuyền và công trình ven biển.")
        elif wspd >= 10.8:
            alerts.append("⚠️ Gió cấp 6 (≥10.8 m/s): gió mạnh, nguy hiểm cho tàu thuyền nhỏ.")

    # --- Gió giật ---
    if gust is not None and gust >= 20:
        alerts.append(f"⚠️ Gió giật mạnh {gust:.1f} m/s ≈ {gust*3.6:.1f} km/h, cần hạn chế ra ngoài.")

    # --- Gió trung bình ngày ---
    if avg_wspd is not None:
        if avg_wspd >= 30:
            alerts.append("⚠️ Gió trung bình mạnh trong ngày (≥30 m/s): nguy hiểm cho tàu thuyền và hoạt động ngoài trời.")
        elif avg_wspd >= 24.5:
            alerts.append("⚠️ Gió trung bình cao trong ngày (≥24.5 m/s): có dấu hiệu bão, cần cảnh giác.")

    # --- Hướng gió (8 hướng chính) ---
    if dir is not None:
        if 0 <= dir < 45 or dir >= 315:
            alerts.append("ℹ️ Gió Bắc: thường mang không khí lạnh, dễ gây rét.")
        elif 45 <= dir < 90:
            alerts.append("ℹ️ Gió Đông Bắc: thường kèm thời tiết lạnh và khô.")
        elif 90 <= dir < 135:
            alerts.append("ℹ️ Gió Đông: mang hơi ẩm từ biển, dễ gây oi bức.")
        elif 135 <= dir < 180:
            alerts.append("ℹ️ Gió Đông Nam: mang theo hơi ẩm, dễ gây oi bức.")
        elif 180 <= dir < 225:
            alerts.append("ℹ️ Gió Nam: thường mang không khí nóng ẩm.")
        elif 225 <= dir < 270:
            alerts.append("ℹ️ Gió Tây Nam: thường kèm mưa lớn, nguy cơ bão nhiệt đới.")
        elif 270 <= dir < 315:
            alerts.append("ℹ️ Gió Tây: khô nóng, dễ gây oi bức.")

    return alerts

# -------------------------------
# 4. ☁️ Cảnh báo Mây
# -------------------------------
def generate_cloud_alerts(cloud: float = None, avg_cloud: float = None) -> List[str]:
    alerts = []
    if cloud is not None:
        if cloud >= 90:
            alerts.append("⚠️ Trời u ám, mây dày đặc (≥90%), ánh sáng hạn chế, ảnh hưởng hoạt động ngoài trời.")
        elif cloud <= 10:
            alerts.append("ℹ️ Trời quang đãng, hầu như không có mây, cần lưu ý nắng gắt.")
    if avg_cloud is not None and avg_cloud >= 85:
        alerts.append("⚠️ Độ che phủ mây trung bình ngày rất cao, trời u ám kéo dài.")
    return alerts

# -------------------------------
# 5. 🌫️ Cảnh báo Điểm sương
# -------------------------------
def generate_dewpoint_alerts(dew: float = None, avg_dew: float = None) -> List[str]:
    alerts = []
    if dew is not None:
        if dew >= 24:
            alerts.append("⚠️ Điểm sương rất cao (≥24°C): không khí ngột ngạt, nguy cơ oi bức và sốc nhiệt.")
        elif dew <= 5:
            alerts.append("⚠️ Điểm sương rất thấp (≤5°C): không khí khô hanh, dễ gây bệnh hô hấp.")
    if avg_dew is not None and avg_dew >= 22:
        alerts.append("⚠️ Điểm sương trung bình ngày cao (≥22°C): không khí ẩm ướt, dễ oi bức.")
    return alerts

# -------------------------------
# 6. 👀 Cảnh báo Tầm nhìn
# -------------------------------
def generate_visibility_alerts(vis: float = None) -> List[str]:
    alerts = []
    if vis is not None:
        if vis < 1:
            alerts.append("⚠️ Tầm nhìn rất hạn chế (<1 km), nguy hiểm khi di chuyển.")
        elif vis < 5:
            alerts.append("⚠️ Tầm nhìn kém (<5 km), cần thận trọng khi lái xe.")
    return alerts

# -------------------------------
# 7. 💧 Cảnh báo Độ ẩm
# -------------------------------
def generate_humidity_alerts(rh: float = None, avg_rh: float = None) -> List[str]:
    alerts = []
    if rh is not None:
        if rh >= 90:
            alerts.append("⚠️ Độ ẩm hiện tại rất cao (≥90%), không khí ngột ngạt, dễ gây oi bức.")
        elif rh <= 30:
            alerts.append("⚠️ Độ ẩm hiện tại rất thấp (≤30%), không khí khô hanh, dễ gây bệnh hô hấp.")
    if avg_rh is not None:
        if avg_rh >= 85:
            alerts.append("⚠️ Độ ẩm trung bình ngày cao (≥85%), không khí ẩm ướt kéo dài.")
        elif avg_rh <= 35:
            alerts.append("⚠️ Độ ẩm trung bình ngày thấp (≤35%), không khí khô hanh kéo dài.")
    return alerts

# -------------------------------
# 8. ⚖️ Cảnh báo Áp suất
# -------------------------------
def generate_pressure_alerts(pmsl: float = None, avg_pmsl: float = None) -> List[str]:
    alerts = []
    if pmsl is not None:
        if pmsl < 1000:
            alerts.append("⚠️ Áp suất thấp (<1000 hPa), có thể ảnh hưởng sức khỏe người già và trẻ nhỏ.")
        elif pmsl > 1025:
            alerts.append("⚠️ Áp suất cao bất thường (>1025 hPa), có thể gây khó chịu, đau đầu hoặc ảnh hưởng tuần hoàn.")
    if avg_pmsl is not None:
        if avg_pmsl < 1000:
            alerts.append("⚠️ Áp suất trung bình ngày thấp (<1000 hPa), có thể ảnh hưởng sức khỏe.")
        elif avg_pmsl > 1025:
            alerts.append("⚠️ Áp suất trung bình ngày cao (>1025 hPa), có thể ảnh hưởng sức khỏe tim mạch.")
    return alerts

# -------------------------------
# 9. 🔆 Cảnh báo Bức xạ mặt trời (luôn có thông tin)
# -------------------------------
def generate_solar_alerts(solar: float = None, avg_solar: float = None) -> List[str]:
    alerts = []
    if solar is not None:
        if solar >= 800:
            alerts.append("⚠️ Bức xạ mặt trời cao (≥800 W/m²), nguy cơ cháy nắng và ảnh hưởng sức khỏe.")
        else:
            alerts.append("🙂 Bức xạ mặt trời hiện tại thấp, an toàn khi ra ngoài.")
    if avg_solar is not None:
        if avg_solar >= 600:
            alerts.append("⚠️ Bức xạ mặt trời trung bình ngày cao (≥600 W/m²), cần hạn chế phơi nắng lâu.")
        else:
            alerts.append("🙂 Bức xạ mặt trời trung bình ngày thấp, không gây nguy hại.")
    return alerts

# -------------------------------
# 10. ☀️ Cảnh báo UV (luôn có thông tin)
# -------------------------------
def generate_uv_alerts(uv: float = None, avg_uv: float = None, uv_max_day: float = None) -> List[str]:
    alerts = []
    # UV hiện tại
    if uv is not None:
        if uv >= 7:
            alerts.append("⚠️ Chỉ số UV rất cao (≥7), cần bảo vệ da khi ra nắng.")
        else:
            alerts.append("🙂 Chỉ số UV hiện tại thấp, an toàn khi ra ngoài.")
    # UV trung bình ngày
    if avg_uv is not None:
        if avg_uv >= 5:
            alerts.append("⚠️ UV trung bình cao trong ngày (≥5), cần bảo vệ da khi hoạt động ngoài trời.")
        else:
            alerts.append("🙂 UV trung bình ngày thấp, không gây nguy hại.")
    # UV tối đa ngày
    if uv_max_day is not None:
        if uv_max_day >= 11:
            alerts.append("⚠️ UV tối đa trong ngày ở mức cực đoan (≥11), tránh nắng hoàn toàn.")
        elif uv_max_day >= 8:
            alerts.append("⚠️ UV tối đa trong ngày rất cao (≥8), hạn chế ra ngoài, che chắn da.")
        elif uv_max_day >= 6:
            alerts.append("ℹ️ UV tối đa trong ngày cao (≥6), nên dùng kem chống nắng.")
        else:
            alerts.append("🙂 UV tối đa trong ngày thấp, khá an toàn.")
    return alerts

# -------------------------------
# Hàm tổng hợp: gọi cả 10 nhóm
# -------------------------------
def generate_all_alerts(unified: Dict[str, Any]) -> List[str]:
    alerts = []

    # --- 🌡️ Cảnh báo nhiệt độ ---
    alerts.extend(generate_temperature_alerts(
        temp=unified.get("temperature"),
        feels=unified.get("apparent_temperature"),
        tmin=unified.get("temperature_2m_min_day"),
        tmax=unified.get("temperature_2m_max_day"),
        avg_temp=unified.get("avg_temperature_day"),
        avg_temp_hour=unified.get("avg_temperature_hourly")
    ))

    # --- 🌧️ Cảnh báo mưa ---
    alerts.extend(generate_rain_alerts(
        rain=unified.get("precipitation_now"),
        rain_prob=unified.get("precipitation_probability_now"),
        avg_rain=unified.get("avg_precipitation_day"),
        avg_rain_hour=unified.get("avg_precipitation_hourly"),
        rain_total_day=unified.get("precipitation_sum_day"),
        gust=unified.get("gust"),
        terrain=unified.get("terrain")
    ))

    # --- 💨 Cảnh báo gió ---
    alerts.extend(generate_wind_alerts(
        wspd=unified.get("wind_speed_now"),
        gust=unified.get("gust"),
        avg_wspd=unified.get("avg_wind_speed_day")
    ))

    # --- ☁️ Cảnh báo mây ---
    alerts.extend(generate_cloud_alerts(
        cloud=unified.get("cloudcover_now"),
        avg_cloud=unified.get("cloudcover_mean")
    ))

    # --- 🌫️ Cảnh báo điểm sương ---
    alerts.extend(generate_dewpoint_alerts(
        dew=unified.get("dewpoint_now"),
        avg_dew=unified.get("dewpoint_mean")
    ))

    # --- 👀 Cảnh báo tầm nhìn ---
    alerts.extend(generate_visibility_alerts(
        vis=unified.get("visibility_now")
    ))

    # --- 💧 Cảnh báo độ ẩm ---
    alerts.extend(generate_humidity_alerts(
        rh=unified.get("humidity_now"),
        avg_rh=unified.get("avg_humidity")
    ))

    # --- ⚖️ Cảnh báo áp suất ---
    alerts.extend(generate_pressure_alerts(
        pmsl=unified.get("pressure_now"),
        avg_pmsl=unified.get("avg_pressure")
    ))

    # --- 🔆 Cảnh báo bức xạ mặt trời ---
    alerts.extend(generate_solar_alerts(
        solar=unified.get("solar_now"),
        avg_solar=unified.get("avg_solar")
    ))

    # --- ☀️ Cảnh báo UV ---
    alerts.extend(generate_uv_alerts(
        uv=unified.get("uv_now"),
        avg_uv=unified.get("avg_uv"),
        uv_max_day=unified.get("uv_max_day")
    ))

    return alerts

# -------------------------------
# Cảnh báo riêng cho khối hiện tại
# -------------------------------
def generate_current_alerts(values: Dict[str, Any]) -> List[str]:
    alerts: List[str] = ["⏱️ CẢNH BÁO TÌNH HÌNH HIỆN TẠI:"]

    # 🌡️ Nhiệt độ + UV tức thời
    temp_alerts = generate_temperature_alerts(
        temp=values.get("temperature"),
        feels=values.get("apparent_temperature"),
        avg_temp_hour=values.get("avg_temperature_hourly")
    )
    alerts.extend([f"⚠️ {a}" for a in temp_alerts])

    uv_alerts = generate_uv_alerts(
        uv=values.get("uv_now")
    )
    alerts.extend([f"⚠️ {a}" for a in uv_alerts])

    # 🌧️ Mưa tức thời
    rain_alerts = generate_rain_alerts(
        rain=values.get("rain"),
        rain_prob=values.get("rain_prob"),
        avg_rain_hour=values.get("avg_precipitation_hourly"),
        gust=values.get("gust"),
        terrain=values.get("terrain")
    )
    alerts.extend([f"⚠️ {a}" for a in rain_alerts])

    # 💨 Gió hiện tại và gió giật
    wind_alerts = generate_wind_alerts(
        wspd=values.get("wspd"),
        gust=values.get("gust")
    )
    alerts.extend([f"⚠️ {a}" for a in wind_alerts])

    # ☁️ Mây
    cloud_alerts = generate_cloud_alerts(cloud=values.get("cloudcover"))
    alerts.extend([f"⚠️ {a}" for a in cloud_alerts])

    # 🌫️ Điểm sương
    dew_alerts = generate_dewpoint_alerts(dew=values.get("dewpoint"))
    alerts.extend([f"⚠️ {a}" for a in dew_alerts])

    # 👀 Tầm nhìn
    vis_alerts = generate_visibility_alerts(vis=values.get("visibility_now"))
    alerts.extend([f"⚠️ {a}" for a in vis_alerts])

    # 💧 Độ ẩm
    humidity_alerts = generate_humidity_alerts(rh=values.get("humidity"))
    alerts.extend([f"⚠️ {a}" for a in humidity_alerts])

    # ⚖️ Áp suất
    pressure_alerts = generate_pressure_alerts(pmsl=values.get("pressure"))
    alerts.extend([f"⚠️ {a}" for a in pressure_alerts])

    # 🔆 Bức xạ mặt trời
    solar_alerts = generate_solar_alerts(solar=values.get("solar"))
    alerts.extend([f"⚠️ {a}" for a in solar_alerts])

    if len(alerts) == 1:
        alerts.append("✅ Không có cảnh báo đặc biệt cho tình hình hiện tại.")
    return alerts


# -------------------------------
# Cảnh báo riêng cho khối tổng quan trong ngày
# -------------------------------
def generate_overview_alerts(values: Dict[str, Any]) -> List[str]:
    alerts: List[str] = ["📅 CẢNH BÁO TỔNG QUAN TRONG NGÀY:"]

    # 🌡️ Nhiệt độ trung bình ngày
    temp_alerts = generate_temperature_alerts(
        tmin=values.get("tmin"),
        tmax=values.get("tmax"),
        avg_temp=values.get("avg_temperature")
    )
    alerts.extend([f"⚠️ {a}" for a in temp_alerts])

    # ☀️ UV trung bình / tối đa ngày
    uv_alerts = generate_uv_alerts(
        avg_uv=values.get("avg_uv"),
        uv_max_day=values.get("uv_max_day")
    )
    alerts.extend([f"⚠️ {a}" for a in uv_alerts])

    # 🌧️ Mưa tổng quan trong ngày
    rain_alerts = generate_rain_alerts(
        rain_total_day=values.get("rain_total_day"),
        avg_rain=values.get("avg_rain"),
        terrain=values.get("terrain")
    )
    alerts.extend([f"⚠️ {a}" for a in rain_alerts])

    # 💨 Gió trung bình ngày
    wind_alerts = generate_wind_alerts(avg_wspd=values.get("avg_wind_speed"))
    alerts.extend([f"⚠️ {a}" for a in wind_alerts])

    # ☁️ Mây trung bình ngày
    cloud_alerts = generate_cloud_alerts(avg_cloud=values.get("cloudcover_mean"))
    alerts.extend([f"⚠️ {a}" for a in cloud_alerts])

    # 🌫️ Điểm sương trung bình ngày
    dew_alerts = generate_dewpoint_alerts(avg_dew=values.get("dewpoint_mean"))
    alerts.extend([f"⚠️ {a}" for a in dew_alerts])

    # 👀 Tầm nhìn trung bình ngày
    vis_alerts = generate_visibility_alerts(vis=values.get("visibility_now"))
    alerts.extend([f"⚠️ {a}" for a in vis_alerts])

    # 💧 Độ ẩm trung bình ngày
    humidity_alerts = generate_humidity_alerts(avg_rh=values.get("avg_humidity"))
    alerts.extend([f"⚠️ {a}" for a in humidity_alerts])

    # ⚖️ Áp suất trung bình ngày
    pressure_alerts = generate_pressure_alerts(avg_pmsl=values.get("avg_pressure"))
    alerts.extend([f"⚠️ {a}" for a in pressure_alerts])

    # 🔆 Bức xạ mặt trời trung bình ngày
    solar_alerts = generate_solar_alerts(avg_solar=values.get("avg_solar"))
    alerts.extend([f"⚠️ {a}" for a in solar_alerts])

    if len(alerts) == 1:
        alerts.append("✅ Không có cảnh báo đặc biệt cho tổng quan trong ngày.")
    return alerts