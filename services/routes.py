# services/routes.py
import logging
from fastapi import APIRouter, Query
from typing import Dict, Any

from services.helpers import geocode_region, reverse_geocode
from services.bulletin import build_bulletin_unified

router = APIRouter()
log = logging.getLogger("WeatherWindy")

# --------------------------------------
# Route /v1/chat
# --------------------------------------
@router.get("/chat")
async def chat(region: str = Query(..., description="Tên địa danh tiếng Việt hoặc lat,lon")) -> Dict[str, Any]:
    """
    Trả về bản tin thời tiết hợp nhất (unified) cho địa danh.
    Luôn dùng build_bulletin_unified để hiển thị bản tin gọn gàng.
    """
    try:
        loc = geocode_region(region)
        lat, lon = float(loc["latitude"]), float(loc["longitude"])
        bulletin = await build_bulletin_unified(lat, lon, loc)   # ✅ await
        return {"status": "ok", "data": {"bulletin": bulletin, "loc": loc}}
    except Exception as e:
        log.error(f"Lỗi khi xử lý /chat: {e}")
        return {"status": "error", "message": str(e)}

# --------------------------------------
# Route /v1/reverse
# --------------------------------------
@router.get("/reverse")
async def reverse(
    lat: float = Query(..., description="Vĩ độ"),
    lon: float = Query(..., description="Kinh độ")
) -> Dict[str, Any]:
    """
    Tra ngược từ tọa độ (lat, lon) sang địa danh bằng Open-Meteo Reverse Geocoding API.
    """
    try:
        loc = reverse_geocode(lat, lon)
        if "error" in loc:
            raise ValueError(loc["error"])
        return {"status": "ok", "data": {"loc": loc}}
    except Exception as e:
        log.error(f"Lỗi khi xử lý /reverse: {e}")
        return {"status": "error", "message": str(e)}