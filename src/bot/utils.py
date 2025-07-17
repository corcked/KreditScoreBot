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
    
    # Проверяем различные форматы
    # Узбекистан
    if len(digits) == 12 and digits.startswith('998'):
        return f"+{digits}"
    elif len(digits) == 9 and digits.startswith('9'):
        return f"+998{digits}"
    
    # Россия
    elif len(digits) == 11 and digits.startswith('7'):
        return f"+{digits}"
    elif len(digits) == 10 and digits.startswith('9'):
        return f"+7{digits}"
    elif len(digits) == 11 and digits.startswith('8'):
        # Заменяем 8 на +7 для российских номеров
        return f"+7{digits[1:]}"
    
    # Международный формат с плюсом
    elif len(digits) >= 10 and len(digits) <= 15:
        # Принимаем любой международный номер разумной длины
        return f"+{digits}"
    
    return None


def validate_amount(text: str, max_amount: int, translate=None) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """
    Валидация суммы
    
    Args:
        text: Введенный текст
        max_amount: Максимальная сумма
        translate: Функция перевода
        
    Returns:
        (валидна, сумма, сообщение об ошибке)
    """
    _ = translate if translate else lambda x: x
    try:
        # Удаляем пробелы и запятые
        clean_text = text.replace(' ', '').replace(',', '')
        amount = Decimal(clean_text)
        
        if amount <= 0:
            return False, None, _('Amount must be positive')
        
        if amount > max_amount:
            return False, None, f"{_('Maximum amount')}: {format_amount(max_amount)} {_('sum')}"
        
        return True, amount, None
    except:
        return False, None, _('Enter correct amount (numbers only)')


def validate_rate(text: str, min_rate: Decimal, max_rate: Decimal, translate=None) -> Tuple[bool, Optional[Decimal], Optional[str]]:
    """
    Валидация процентной ставки
    
    Returns:
        (валидна, ставка, сообщение об ошибке)
    """
    _ = translate if translate else lambda x: x
    try:
        rate = Decimal(text.replace(',', '.'))
        
        if rate < min_rate or rate > max_rate:
            return False, None, f"{_('Rate must be between')} {min_rate}% {_('and')} {max_rate}%"
        
        return True, rate, None
    except:
        return False, None, _('Enter correct interest rate')


def validate_term(text: str, min_months: int, max_months: int, translate=None) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Валидация срока кредита
    
    Returns:
        (валиден, срок в месяцах, сообщение об ошибке)
    """
    _ = translate if translate else lambda x: x
    try:
        months = int(text)
        
        if months < min_months or months > max_months:
            return False, None, f"{_('Term must be from')} {min_months} {_('to')} {max_months} {_('months')}"
        
        return True, months, None
    except:
        return False, None, _('Enter number of months (numbers only)')


def validate_age(text: str, translate=None) -> Tuple[bool, Optional[int], Optional[str]]:
    """Валидация возраста"""
    _ = translate if translate else lambda x: x
    try:
        age = int(text)
        
        if age < 18:
            return False, None, _('You must be over 18 years old')
        
        if age > 100:
            return False, None, _('Enter correct age')
        
        return True, age, None
    except:
        return False, None, _('Enter age (numbers only)')


def validate_positive_number(text: str, field_name: str, translate=None) -> Tuple[bool, Optional[int], Optional[str]]:
    """Валидация положительного числа"""
    _ = translate if translate else lambda x: x
    try:
        number = int(text)
        
        if number < 0:
            return False, None, f"{field_name} {_('cannot be negative')}"
        
        return True, number, None
    except:
        return False, None, f"{_('Enter')} {field_name.lower()} {_('(numbers only)')}"


def format_amount(amount: Decimal) -> str:
    """Форматирование суммы для отображения"""
    return f"{amount:,.0f}".replace(",", " ")


def format_loan_summary(loan_data: dict, translate=None) -> str:
    """Форматирование сводки по кредиту"""
    _ = translate if translate else lambda x: x
    loan_type = _('Car loan') if loan_data["loan_type"] == "carloan" else _('Microloan')
    
    summary = f"**{loan_type}**\n\n"
    summary += f"💰 {_('Amount')}: {format_amount(loan_data['amount'])} {_('sum')}\n"
    summary += f"📊 {_('Rate')}: {loan_data['rate']}%\n"
    summary += f"📅 {_('Term')}: {loan_data['term_months']} {_('months')}\n"
    summary += f"💳 {_('Monthly payment')}: {format_amount(loan_data['monthly_payment'])} {_('sum')}\n"
    summary += f"💸 {_('Income')}: {format_amount(loan_data['income'])} {_('sum')}\n"
    
    if loan_data.get('other_payments'):
        summary += f"💵 {_('Other payments')}: {format_amount(loan_data['other_payments'])} {_('sum')}\n"
    
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