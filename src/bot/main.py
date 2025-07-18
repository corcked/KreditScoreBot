import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.bot.handlers import bank_flow, loan, onboarding, personal_data, referral, score, settings
from src.bot.middleware.i18n import I18nMiddleware
from src.bot.middleware.rate_limit import RateLimitMiddleware
from src.config.settings import settings as app_settings
from src.db.database import close_db, init_db

# Настройка логирования
logging.basicConfig(
    level=getattr(logging, app_settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def on_startup():
    """Действия при запуске бота"""
    logger.info("Starting bot...")
    await init_db()
    logger.info("Database initialized")


async def on_shutdown():
    """Действия при остановке бота"""
    logger.info("Shutting down bot...")
    await close_db()
    logger.info("Database connection closed")


async def main():
    """Основная функция запуска бота"""
    # Инициализация бота и диспетчера
    bot = Bot(token=app_settings.bot_token, parse_mode="Markdown")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Сбрасываем webhook при старте (на случай если он был установлен)
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Webhook deleted, starting polling mode")
    
    # Регистрация middleware
    dp.message.middleware(I18nMiddleware())
    dp.callback_query.middleware(I18nMiddleware())
    dp.message.middleware(RateLimitMiddleware())
    dp.callback_query.middleware(RateLimitMiddleware())
    
    # Регистрация роутеров
    dp.include_router(onboarding.router)
    dp.include_router(loan.router)
    dp.include_router(personal_data.router)
    dp.include_router(referral.router)
    dp.include_router(bank_flow.router)
    dp.include_router(score.router)
    dp.include_router(settings.router)
    
    # Установка команд бота
    from aiogram.types import BotCommand
    
    await bot.set_my_commands([
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="menu", description="Главное меню"),
        BotCommand(command="my_app", description="Моя заявка"),
        BotCommand(command="score", description="Мои показатели"),
        BotCommand(command="invite", description="Реферальная программа"),
        BotCommand(command="help", description="Помощь"),
    ])
    
    # Регистрация хуков
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Запуск бота
    try:
        if app_settings.webhook_enabled:
            # Webhook режим для продакшена
            logger.info(f"Starting webhook on {app_settings.webhook_url}")
            # Здесь должна быть настройка webhook
            # await bot.set_webhook(app_settings.webhook_url + app_settings.get_webhook_path())
            # Но для простоты используем polling
            await dp.start_polling(bot)
        else:
            # Polling режим для разработки
            logger.info("Starting polling...")
            await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped")
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)