from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from sqlalchemy import select

from src.bot.i18n import I18nContext, get_user_language, simple_gettext
from src.db.database import get_db_context
from src.db.models import User


class I18nMiddleware(BaseMiddleware):
    """Middleware для обработки локализации"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # Определяем пользователя
        user = None
        if isinstance(event, (Message, CallbackQuery)):
            user = event.from_user
        
        # Получаем сохраненный язык из БД
        user_language = None
        if user:
            async with get_db_context() as db:
                result = await db.execute(
                    select(User).where(User.telegram_id == user.id)
                )
                db_user = result.scalar_one_or_none()
                if db_user:
                    user_language = db_user.language_code
        
        # Определяем язык
        lang_code = get_user_language(user, user_language)
        
        # Создаем контекст i18n
        i18n = I18nContext(lang_code)
        
        # Добавляем в data для использования в хендлерах
        data["i18n"] = i18n
        data["_"] = lambda msg: simple_gettext(lang_code, msg)  # Упрощенная функция перевода
        
        # Вызываем хендлер
        return await handler(event, data)