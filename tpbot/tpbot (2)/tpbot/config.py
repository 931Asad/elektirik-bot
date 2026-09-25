import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()
}
DB_PATH = os.getenv("DB_PATH", "tpbot.db")

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN topilmadi. .env faylini tekshiring (.env.example dan nusxa oling).")

if not ADMIN_IDS:
    raise RuntimeError("ADMIN_IDS topilmadi. .env fayliga o'z Telegram ID'ingizni yozing.")
