import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8717585554:AAEFBzT6bHaUtgjOvLyTvGBc5J5wPL1VdXw")
OWNER_ID = int(os.getenv("OWNER_ID", "7761880504"))
OWNER_USERNAME = "@gensshstore"
DB_PATH = os.getenv("DB_PATH", "database/vps_store.db")
QRIS_DIR = os.getenv("QRIS_DIR", "assets")
