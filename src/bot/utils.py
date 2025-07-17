import re
from decimal import Decimal
from typing import Optional, Tuple

from aiogram import Bot
from aiogram.types import User as TelegramUser

from src.core.enums import DeviceType


def validate_phone_number(phone: str) -> Optional[str]:
    """
    Валидация и нормализация номера телефона
    
    Args:
        phone: Номер телефона
        
    Returns:
        Нормализованный номер или None
    """
    # Удаляем все не-цифры
    digits = re.sub(r'\D', '', phone)
    
    # Проверяем длину и формат (для Узбекистана)
    if len(digits) == 12 and digits.startswith('998'):
        return f"+{digits}"
    elif len(digits) == 9 and digits.startswith('9'):
        return f"+998{digits}"
    
    return None


def validate_amount(text: str, max_amount: int) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """
    Валидация суммы
    
    Args:
        text: Введенный текст
        max_amount: Максимальная сумма
        
    Returns:
        (валидна, сумма, сообщение об ошибке)
    """
    try:
        # Удаляем пробелы и запятые
        clean_text = text.replace(' ', '').replace(',', '')
        amount = Decimal(clean_text)
        
        if amount <= 0:
            return False, None, "Сумма должна быть положительной"
        
        if amount > max_amount:
            return False, None, f"Максимальная сумма: {format_amount(max_amount)} сум"
        
        return True, amount, None
    except:
        return False, None, "Введите корректную сумму (только цифры)"


def validate_rate(text: str, min_rate: Decimal, max_rate: Decimal) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """
    Валидация процентной ставки
    
    Returns:
        (валидна, ставка, сообщение об ошибке)
    """
    try:
        rate = Decimal(text.replace(',', '.'))
        
        if rate < min_rate or rate > max_rate:
            return False, None, f"Ставка должна быть от {min_rate}% до {max_rate}%"
        
        return True, rate, None
    except:
        return False, None, "Введите корректную процентную ставку"


def validate_term(text: str, min_months: int, max_months: int) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Валидация срока кредита
    
    Returns:
        (валиден, срок в месяцах, сообщение об ошибке)
    """
    try:
        months = int(text)
        
        if months < min_months or months > max_months:
            return False, None, f"Срок должен быть от {min_months} до {max_months} месяцев"
        
        return True, months, None
    except:
        return False, None, "Введите количество месяцев (только цифры)"


def validate_age(text: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Валидация возраста"""
    try:
        age = int(text)
        
        if age < 18:
            return False, None, "Вы должны быть старше 18 лет"
        
        if age > 100:
            return False, None, "Введите корректный возраст"
        
        return True, age, None
    except:
        return False, None, "Введите возраст (только цифры)"


def validate_positive_number(text: str, field_name: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """Валидация положительного числа"""
    try:
        number = int(text)
        
        if number < 0:
            return False, None, f"{field_name} не может быть отрицательным"
        
        return True, number, None
    except:
        return False, None, f"Введите {field_name.lower()} (только цифры)"


def format_amount(amount: Decimal) -> str:
    """Форматирование суммы для отображения"""
    return f"{amount:,.0f}".replace(",", " ")


def format_loan_summary(loan_data: dict) -> str:
    """Форматирование сводки по кредиту"""
    loan_type = "Автокредит" if loan_data["loan_type"] == "carloan" else "Микрозайм"
    
    summary = f"**{loan_type}**\n\n"
    summary += f"💰 Сумма: {format_amount(loan_data['amount'])} сум\n"
    summary += f"📊 Ставка: {loan_data['rate']}%\n"
    summary += f"📅 Срок: {loan_data['term_months']} мес.\n"
    summary += f"💳 Ежемесячный платеж: {format_amount(loan_data['monthly_payment'])} сум\n"
    summary += f"💸 Доход: {format_amount(loan_data['income'])} сум\n"
    
    if loan_data.get('other_payments'):
        summary += f"💵 Другие платежи: {format_amount(loan_data['other_payments'])} сум\n"
    
    return summary


def detect_device_type(user: TelegramUser) -> DeviceType:
    """
    Определение типа устройства пользователя
    
    Это упрощенная версия - в реальности нужен более сложный анализ
    """
    # В Telegram Bot API нет прямого способа определить устройство
    # Это заглушка для демонстрации
    return DeviceType.OTHER


def escape_markdown(text: str) -> str:
    """Экранирование специальных символов для Markdown"""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


async def notify_admins(bot: Bot, message: str, admin_ids: list[int]) -> None:
    """Отправка уведомлений администраторам"""
    for admin_id in admin_ids:
        try:
            await bot.send_message(admin_id, message, parse_mode="Markdown")
        except Exception:
            # Игнорируем ошибки отправки отдельным админам
            pass