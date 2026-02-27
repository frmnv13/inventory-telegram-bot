import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME")
}

ADMIN_IDS_STR = os.getenv("ADMIN_USER_IDS", "")
ADMIN_USER_IDS = [int(user_id) for user_id in ADMIN_IDS_STR.split(',') if user_id.strip().isdigit()]

