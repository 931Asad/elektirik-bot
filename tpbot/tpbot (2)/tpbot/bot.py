import asyncio
import logging
import os

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from database import init_db
from handlers import admin, search


async def _handle_ping(request):
    # Render/UptimeRobot shu manzilga "tirikmisan" deb so'rab turadi.
    return web.Response(text="Bot ishlab turibdi ✅")


async def _start_keepalive_server():
    """Render kabi xizmatlar uchun: botning 'uxlab qolmasligi' uchun
    kichik veb-server ochamiz, UptimeRobot shu manzilni doim so'rab turadi."""
    app = web.Application()
    app.router.add_get("/", _handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logging.info(f"Keepalive server {port}-portda ishga tushdi")


async def main():
    logging.basicConfig(level=logging.INFO)
    init_db()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # admin.py birinchi bo'lishi kerak: /add, /addline kabi buyruqlar
    # va FSM holatlari search.py'dagi umumiy matn handleridan oldin ishlashi uchun
    dp.include_router(admin.router)
    dp.include_router(search.router)

    await bot.delete_webhook(drop_pending_updates=True)

    # Render'da PORT muhit o'zgaruvchisi bo'lsa, keepalive serverni ham ishga tushiramiz.
    # Oddiy kompyuterda (PORT yo'q bo'lsa ham) bu zararsiz, shunchaki 10000-portda ochiladi.
    await _start_keepalive_server()

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
