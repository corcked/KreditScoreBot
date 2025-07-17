import asyncio
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from cachetools import TTLCache

from src.config.settings import settings


class RateLimitMiddleware(BaseMiddleware):
    """Middleware для ограничения частоты запросов"""

    def __init__(
        self,
        messages_per_minute: int = None,
        commands_per_minute: int = None,
        storage_time: int = 120,  # Время хранения в секундах
    ):
        self.messages_per_minute = messages_per_minute or settings.rate_limit_messages_per_minute
        self.commands_per_minute = commands_per_minute or settings.rate_limit_commands_per_minute
        
        # Кэш для хранения истории запросов
        self.message_storage = TTLCache(maxsize=10000, ttl=storage_time)
        self.command_storage = TTLCache(maxsize=10000, ttl=storage_time)
        
        # Блокировка для потокобезопасности
        self.lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Обработка события"""
        user_id = self._get_user_id(event)
        
        if not user_id:
            return await handler(event, data)

        # Проверяем лимиты
        is_command = self._is_command(event)
        
        async with self.lock:
            if is_command:
                if not await self._check_limit(user_id, self.command_storage, self.commands_per_minute):
                    await self._send_limit_message(event, "команд")
                    return
            else:
                if not await self._check_limit(user_id, self.message_storage, self.messages_per_minute):
                    await self._send_limit_message(event, "сообщений")
                    return

        return await handler(event, data)

    def _get_user_id(self, event: TelegramObject) -> Optional[int]:
        """Получение ID пользователя из события"""
        if isinstance(event, Message):
            return event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            return event.from_user.id
        return None

    def _is_command(self, event: TelegramObject) -> bool:
        """Проверка, является ли событие командой"""
        if isinstance(event, Message):
            return bool(event.text and event.text.startswith('/'))
        return False

    async def _check_limit(
        self,
        user_id: int,
        storage: TTLCache,
        limit: int
    ) -> bool:
        """
        Проверка лимита запросов
        
        Returns:
            True если лимит не превышен
        """
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)
        
        # Получаем историю запросов пользователя
        user_history = storage.get(user_id, [])
        
        # Удаляем старые записи
        user_history = [timestamp for timestamp in user_history if timestamp > minute_ago]
        
        # Проверяем лимит
        if len(user_history) >= limit:
            return False
        
        # Добавляем текущий запрос
        user_history.append(now)
        storage[user_id] = user_history
        
        return True

    async def _send_limit_message(self, event: TelegramObject, limit_type: str) -> None:
        """Отправка сообщения о превышении лимита"""
        message = (
            f"⚠️ Превышен лимит {limit_type} в минуту.\n"
            f"Пожалуйста, подождите немного перед следующим запросом."
        )
        
        if isinstance(event, Message):
            await event.answer(message)
        elif isinstance(event, CallbackQuery):
            await event.answer(message, show_alert=True)