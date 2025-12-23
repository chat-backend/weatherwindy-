# configs.py
import os
from dotenv import load_dotenv

# --------------------------------------
# Nạp biến môi trường từ file .env
# --------------------------------------
load_dotenv()

# --------------------------------------
# Cấu hình chung cho dự án WeatherWindy
# --------------------------------------
APP_NAME: str = os.getenv("APP_NAME", "WeatherWindy")
PORT: int = int(os.getenv("PORT") or 8080)
DEFAULT_TZ: str = os.getenv("DEFAULT_TZ", "Asia/Ho_Chi_Minh")

# --------------------------------------
# API Open-Meteo (nguồn dữ liệu chính)
# --------------------------------------
OPEN_METEO_FORECAST: str = os.getenv(
    "OPEN_METEO_FORECAST",
    "https://api.open-meteo.com/v1/forecast"
)
OPEN_METEO_GEOCODE: str = os.getenv(
    "OPEN_METEO_GEOCODE",
    "https://geocoding-api.open-meteo.com/v1/search"
)
OPEN_METEO_REVERSE: str = os.getenv(
    "OPEN_METEO_REVERSE",
    "https://geocoding-api.open-meteo.com/v1/reverse"
)

# --------------------------------------
# Các trường dữ liệu Open-Meteo (3 cấp độ)
# --------------------------------------
OPEN_METEO_FIELDS_CURRENT: str = os.getenv("OPEN_METEO_FIELDS_CURRENT")
OPEN_METEO_FIELDS_HOURLY: str = os.getenv("OPEN_METEO_FIELDS_HOURLY")
OPEN_METEO_FIELDS_DAILY: str = os.getenv("OPEN_METEO_FIELDS_DAILY")

# --------------------------------------
# Ngôn ngữ và số lượng kết quả geocode
# --------------------------------------
OPEN_METEO_LANG: str = os.getenv("OPEN_METEO_LANG", "vi")
OPEN_METEO_GEOCODE_COUNT: int = int(os.getenv("OPEN_METEO_GEOCODE_COUNT") or 1)

# --------------------------------------
# Timeout cho request
# --------------------------------------
REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT") or 15)

# --------------------------------------
# Cấu hình hợp nhất nguồn dữ liệu
#   "openmeteo"  -> chỉ dùng Open-Meteo
#   "avg"        -> (dự phòng cho nhiều nguồn, hiện tại chỉ có Open-Meteo)
# --------------------------------------
MERGE_STRATEGY: str = os.getenv("MERGE_STRATEGY", "openmeteo")

# --------------------------------------
# Cache TTL (giây)
# --------------------------------------
CACHE_TTL_SECONDS: int = int(os.getenv("CACHE_TTL_SECONDS") or 300)