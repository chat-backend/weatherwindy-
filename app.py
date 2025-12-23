# app.py
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import httpx

# Import cấu hình chung
from configs import APP_NAME, PORT, OPEN_METEO_FORECAST

# Import routers
from services.routes import router as api_router

# Import danh sách địa danh
from vietnam_provinces import PROVINCES
from vietnam_wards import WARDS

# --------------------------------------
# Logging setup
# --------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
log = logging.getLogger(APP_NAME)

# --------------------------------------
# Lifespan events (startup/shutdown)
# --------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(f"✅ {APP_NAME} API starting up...")
    log.info("✅ CORS enabled, endpoints: /v1/chat, /v1/typhoon, /weather")
    log.info(f"✅ Uvicorn running port {PORT} (if launched with uvicorn)")

    # Thống kê tỉnh/thành
    provinces = list(PROVINCES.keys())
    log.info(f"📍 Tổng số tỉnh/thành: {len(provinces)}")  # 34

    # Thống kê phường/xã toàn quốc
    wards_all = list(WARDS.keys())
    log.info(f"📍 Tổng số phường/xã toàn quốc: {len(wards_all)}")  # 3321

    yield
    log.info(f"🛑 {APP_NAME} API shutting down...")

# --------------------------------------
# FastAPI app + CORS
# --------------------------------------
app = FastAPI(title=APP_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # có thể siết chặt khi production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------
# Đăng ký routers
# --------------------------------------
app.include_router(api_router, prefix="/v1")

# --------------------------------------
# Mount static files (nếu có thư mục static)
# --------------------------------------
if os.path.isdir("static"):
    app.mount("/", StaticFiles(directory="static", html=True), name="static")

# --------------------------------------
# Endpoint: /weather
# --------------------------------------
@app.get("/weather")
async def get_weather(
    lat: float = Query(..., description="Vĩ độ"),
    lon: float = Query(..., description="Kinh độ"),
    source: str = Query("openmeteo", description="Nguồn dữ liệu: chỉ Open-Meteo")
):
    """
    Gọi dữ liệu thời tiết từ Open-Meteo.
    - lat, lon: tọa độ địa điểm
    - source: hiện tại chỉ hỗ trợ 'openmeteo'
    """

    results = {}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(
                OPEN_METEO_FORECAST,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "hourly": "temperature_2m,precipitation,wind_speed_10m"
                }
            )
            resp.raise_for_status()
            results["openmeteo"] = resp.json()
        except Exception as e:
            results["openmeteo_error"] = str(e)

    return results