import hashlib
import secrets
from typing import Optional, Tuple
from urllib.parse import urlencode


class ReferralSystem:
    """Система управления реферальными ссылками"""

    # Длина реферального кода
    CODE_LENGTH = 8
    
    # Префикс для deep-link
    DEEPLINK_PREFIX = "ref_"
    
    # Секрет для генерации кодов (в продакшене должен быть в переменных окружения)
    SECRET_SALT = "kreditscore_referral_salt"

    @staticmethod
    def generate_referral_code(user_id: int) -> str:
        """
        Генерация уникального реферального кода для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Реферальный код
        """
        # Создаем уникальную строку на основе user_id и соли
        unique_string = f"{user_id}_{ReferralSystem.SECRET_SALT}"
        
        # Генерируем хеш
        hash_object = hashlib.sha256(unique_string.encode())
        hash_hex = hash_object.hexdigest()
        
        # Берем первые N символов хеша
        return hash_hex[:ReferralSystem.CODE_LENGTH]

    @staticmethod
    def generate_referral_link(bot_username: str, user_id: int) -> str:
        """
        Генерация реферальной ссылки
        
        Args:
            bot_username: Username бота (без @)
            user_id: ID пользователя
            
        Returns:
            Полная реферальная ссылка
        """
        referral_code = ReferralSystem.generate_referral_code(user_id)
        
        # Формируем deep-link параметр
        start_param = f"{ReferralSystem.DEEPLINK_PREFIX}{referral_code}"
        
        # Создаем ссылку
        return f"https://t.me/{bot_username}?start={start_param}"

    @staticmethod
    def parse_referral_code(start_param: str) -> Optional[str]:
        """
        Извлечение реферального кода из параметра start
        
        Args:
            start_param: Параметр start из deep-link
            
        Returns:
            Реферальный код или None
        """
        if not start_param:
            return None
            
        # Проверяем, что параметр начинается с префикса
        if start_param.startswith(ReferralSystem.DEEPLINK_PREFIX):
            return start_param[len(ReferralSystem.DEEPLINK_PREFIX):]
            
        return None

    @staticmethod
    def validate_referral_code(code: str) -> bool:
        """
        Валидация реферального кода
        
        Args:
            code: Реферальный код
            
        Returns:
            True если код валидный
        """
        if not code:
            return False
            
        # Проверяем длину
        if len(code) != ReferralSystem.CODE_LENGTH:
            return False
            
        # Проверяем, что код содержит только допустимые символы (hex)
        try:
            int(code, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def find_referrer_by_code(code: str, user_id: int) -> Optional[int]:
        """
        Поиск реферера по коду
        
        Это заглушка - в реальном приложении здесь должен быть
        поиск в базе данных по всем пользователям
        
        Args:
            code: Реферальный код
            user_id: ID текущего пользователя (чтобы исключить самореферал)
            
        Returns:
            ID реферера или None
        """
        # В реальном приложении здесь должен быть запрос к БД
        # Сейчас просто возвращаем None
        return None

    @staticmethod
    def can_use_referral(new_user_id: int, referrer_id: int) -> Tuple[bool, str]:
        """
        Проверка возможности использования реферальной ссылки
        
        Args:
            new_user_id: ID нового пользователя
            referrer_id: ID реферера
            
        Returns:
            Кортеж (можно_использовать, причина_отказа)
        """
        # Проверка на самореферал
        if new_user_id == referrer_id:
            return False, "Нельзя использовать собственную реферальную ссылку"
            
        # В реальном приложении здесь должны быть дополнительные проверки:
        # - Не был ли пользователь уже зарегистрирован
        # - Не использовал ли он уже чью-то реферальную ссылку
        # - Не превышен ли лимит рефералов
        
        return True, ""

    @staticmethod
    def format_referral_message(link: str, count: int = 0) -> str:
        """
        Форматирование сообщения с реферальной ссылкой
        
        Args:
            link: Реферальная ссылка
            count: Количество приглашенных пользователей
            
        Returns:
            Отформатированное сообщение
        """
        message = "🎁 **Ваша реферальная программа**\\n\\n"
        message += f"Приглашайте друзей и получайте +20 баллов к скорингу за каждого!\\n\\n"
        message += f"📊 Приглашено пользователей: **{count}**\\n\\n"
        message += f"🔗 Ваша персональная ссылка:\\n`{link}`\\n\\n"
        message += "Поделитесь этой ссылкой с друзьями. Когда они зарегистрируются "
        message += "в боте по вашей ссылке, вы автоматически получите бонусные баллы!"
        
        return message

    @staticmethod
    def generate_share_text(link: str) -> str:
        """
        Генерация текста для шаринга
        
        Args:
            link: Реферальная ссылка
            
        Returns:
            Текст для отправки
        """
        text = "🏦 KreditScore - узнай свой кредитный рейтинг!\\n\\n"
        text += "✅ Мгновенный расчет долговой нагрузки\\n"
        text += "✅ Оценка вероятности одобрения кредита\\n"
        text += "✅ Подбор лучших предложений от банков\\n\\n"
        text += f"Начни прямо сейчас: {link}"
        
        return text

    @staticmethod
    def create_share_button_url(link: str) -> str:
        """
        Создание URL для кнопки "Поделиться" в Telegram
        
        Args:
            link: Реферальная ссылка
            
        Returns:
            URL для inline-кнопки
        """
        share_text = ReferralSystem.generate_share_text(link)
        params = {
            'text': share_text
        }
        return f"https://t.me/share/url?{urlencode(params)}"