# /telegram-stock-bot/config.py

import os
from dotenv import load_dotenv

# Muat variabel lingkungan dari file .env
load_dotenv()

# --- Telegram Bot Configuration ---
# Ambil token dari environment variable
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# --- MySQL Database Configuration ---
# Ambil konfigurasi database dari environment variable
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"), # "localhost" adalah nilai default jika DB_HOST tidak ditemukan
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

# --- Admin Configuration ---
# Ambil daftar ID admin yang dipisahkan koma dari environment variable
ADMIN_IDS_STR = os.getenv("ADMIN_USER_IDS", "")
# Ubah menjadi list of integers, abaikan jika ada spasi atau bukan angka
ADMIN_USER_IDS = [int(user_id) for user_id in ADMIN_IDS_STR.split(',') if user_id.strip().isdigit()]
