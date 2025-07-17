import pytest
from urllib.parse import parse_qs, urlparse

from src.core.referral import ReferralSystem


class TestReferralSystem:
    """Тесты для реферальной системы"""

    def test_generate_referral_code(self):
        """Тест генерации реферального кода"""
        # Для одного пользователя код должен быть одинаковым
        code1 = ReferralSystem.generate_referral_code(12345)
        code2 = ReferralSystem.generate_referral_code(12345)
        assert code1 == code2
        
        # Для разных пользователей коды должны отличаться
        code3 = ReferralSystem.generate_referral_code(54321)
        assert code1 != code3
        
        # Проверка длины кода
        assert len(code1) == ReferralSystem.CODE_LENGTH

    def test_generate_referral_link(self):
        """Тест генерации реферальной ссылки"""
        bot_username = "TestBot"
        user_id = 12345
        
        link = ReferralSystem.generate_referral_link(bot_username, user_id)
        
        # Проверяем формат ссылки
        assert link.startswith(f"https://t.me/{bot_username}?start=")
        assert ReferralSystem.DEEPLINK_PREFIX in link
        
        # Проверяем, что код в ссылке соответствует коду пользователя
        code = ReferralSystem.generate_referral_code(user_id)
        expected_param = f"{ReferralSystem.DEEPLINK_PREFIX}{code}"
        assert expected_param in link

    def test_parse_referral_code(self):
        """Тест извлечения реферального кода"""
        code = "abc12345"
        
        # Правильный формат
        start_param = f"{ReferralSystem.DEEPLINK_PREFIX}{code}"
        parsed = ReferralSystem.parse_referral_code(start_param)
        assert parsed == code
        
        # Неправильный префикс
        parsed = ReferralSystem.parse_referral_code(f"wrong_{code}")
        assert parsed is None
        
        # Пустой параметр
        parsed = ReferralSystem.parse_referral_code("")
        assert parsed is None
        
        # None параметр
        parsed = ReferralSystem.parse_referral_code(None)
        assert parsed is None

    def test_validate_referral_code(self):
        """Тест валидации реферального кода"""
        # Валидный код (hex)
        assert ReferralSystem.validate_referral_code("abcd1234") is True
        assert ReferralSystem.validate_referral_code("0123abcd") is True
        
        # Невалидная длина
        assert ReferralSystem.validate_referral_code("abc") is False
        assert ReferralSystem.validate_referral_code("abcd12345") is False
        
        # Невалидные символы
        assert ReferralSystem.validate_referral_code("abcd123g") is False
        assert ReferralSystem.validate_referral_code("abcd-123") is False
        
        # Пустой код
        assert ReferralSystem.validate_referral_code("") is False
        assert ReferralSystem.validate_referral_code(None) is False

    def test_can_use_referral(self):
        """Тест проверки возможности использования реферала"""
        # Самореферал
        can_use, reason = ReferralSystem.can_use_referral(123, 123)
        assert can_use is False
        assert "собственную" in reason
        
        # Разные пользователи
        can_use, reason = ReferralSystem.can_use_referral(123, 456)
        assert can_use is True
        assert reason == ""

    def test_format_referral_message(self):
        """Тест форматирования сообщения с реферальной ссылкой"""
        link = "https://t.me/TestBot?start=ref_abc123"
        count = 5
        
        message = ReferralSystem.format_referral_message(link, count)
        
        assert "реферальная программа" in message
        assert "+20 баллов" in message
        assert f"Приглашено пользователей: **{count}**" in message
        assert link in message

    def test_generate_share_text(self):
        """Тест генерации текста для шаринга"""
        link = "https://t.me/TestBot?start=ref_abc123"
        
        text = ReferralSystem.generate_share_text(link)
        
        assert "KreditScore" in text
        assert "кредитный рейтинг" in text
        assert link in text

    def test_create_share_button_url(self):
        """Тест создания URL для кнопки шаринга"""
        link = "https://t.me/TestBot?start=ref_abc123"
        
        share_url = ReferralSystem.create_share_button_url(link)
        
        # Проверяем базовый URL
        assert share_url.startswith("https://t.me/share/url?")
        
        # Парсим параметры
        parsed = urlparse(share_url)
        params = parse_qs(parsed.query)
        
        # Проверяем, что текст содержит ссылку
        assert "text" in params
        assert link in params["text"][0]

    def test_referral_code_consistency(self):
        """Тест консистентности генерации и парсинга"""
        user_id = 99999
        bot_username = "ConsistencyBot"
        
        # Генерируем ссылку
        link = ReferralSystem.generate_referral_link(bot_username, user_id)
        
        # Извлекаем start параметр из ссылки
        parsed = urlparse(link)
        params = parse_qs(parsed.query)
        start_param = params["start"][0]
        
        # Парсим код из параметра
        parsed_code = ReferralSystem.parse_referral_code(start_param)
        
        # Сравниваем с оригинальным кодом
        original_code = ReferralSystem.generate_referral_code(user_id)
        assert parsed_code == original_code
        
        # Проверяем валидность
        assert ReferralSystem.validate_referral_code(parsed_code) is True