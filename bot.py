import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import bot_token, temp_dir
from database import init_db
from handlers import start_router, watermark_router, verify_router, integrity_router, history_router

# запуск бота
async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    os.makedirs(temp_dir, exist_ok=True)
    await init_db()

    bot = Bot(token=bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start_router)
    dp.include_router(watermark_router)
    dp.include_router(verify_router)
    dp.include_router(integrity_router)
    dp.include_router(history_router)

    logging.info('Бот запущен.')
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logging.info('Бот остановлен.')

if __name__ == '__main__':
    asyncio.run(main())