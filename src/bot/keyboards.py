from typing import List, Optional

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from src.core.enums import (
    CarCondition,
    Education,
    Gender,
    HousingStatus,
    LoanType,
    MaritalStatus,
    ReceiveMethod,
    Region,
)


class Keyboards:
    """Клавиатуры для бота"""

    @staticmethod
    def phone_request() -> ReplyKeyboardMarkup:
        """Клавиатура для запроса номера телефона"""
        keyboard = [
            [KeyboardButton(text="📱 Поделиться номером", request_contact=True)]
        ]
        return ReplyKeyboardMarkup(
            keyboard=keyboard,
            resize_keyboard=True,
            one_time_keyboard=True
        )

    @staticmethod
    def remove() -> ReplyKeyboardRemove:
        """Удаление клавиатуры"""
        return ReplyKeyboardRemove()

    @staticmethod
    def language_choice() -> InlineKeyboardMarkup:
        """Выбор языка"""
        keyboard = [
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Главное меню"""
        keyboard = [
            [InlineKeyboardButton(text="💳 Новая заявка", callback_data="new_loan")],
            [InlineKeyboardButton(text="📋 Мои заявки", callback_data="my_applications")],
            [InlineKeyboardButton(text="👤 Личные данные", callback_data="personal_data")],
            [InlineKeyboardButton(text="🎁 Реферальная программа", callback_data="referral")],
            [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def loan_type_choice() -> InlineKeyboardMarkup:
        """Выбор типа кредита"""
        keyboard = [
            [InlineKeyboardButton(text="🚗 Автокредит", callback_data=f"loan_type:{LoanType.CARLOAN.value}")],
            [InlineKeyboardButton(text="💰 Микрозайм", callback_data=f"loan_type:{LoanType.MICROLOAN.value}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def car_condition_choice() -> InlineKeyboardMarkup:
        """Выбор состояния автомобиля"""
        keyboard = [
            [InlineKeyboardButton(text="✨ Новый", callback_data=f"car:{CarCondition.NEW.value}")],
            [InlineKeyboardButton(text="🚙 Подержанный", callback_data=f"car:{CarCondition.USED.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def receive_method_choice() -> InlineKeyboardMarkup:
        """Выбор способа получения"""
        keyboard = [
            [InlineKeyboardButton(text="💳 На карту", callback_data=f"receive:{ReceiveMethod.CARD.value}")],
            [InlineKeyboardButton(text="💵 Наличными", callback_data=f"receive:{ReceiveMethod.CASH.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def skip_other_payments() -> InlineKeyboardMarkup:
        """Пропустить ввод других платежей"""
        keyboard = [
            [InlineKeyboardButton(text="➡️ Пропустить", callback_data="skip_other_payments")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def confirm_application() -> InlineKeyboardMarkup:
        """Подтверждение заявки"""
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_app"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_app"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def application_actions(can_send: bool = True) -> InlineKeyboardMarkup:
        """Действия с заявкой"""
        keyboard = []
        
        if can_send:
            keyboard.append([InlineKeyboardButton(text="🏦 Отправить в банк", callback_data="send_to_bank")])
        
        keyboard.extend([
            [InlineKeyboardButton(text="👤 Заполнить личные данные", callback_data="fill_personal")],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")],
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def gender_choice() -> InlineKeyboardMarkup:
        """Выбор пола"""
        keyboard = [
            [
                InlineKeyboardButton(text="👨 Мужской", callback_data=f"gender:{Gender.MALE.value}"),
                InlineKeyboardButton(text="👩 Женский", callback_data=f"gender:{Gender.FEMALE.value}"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def yes_no_choice(prefix: str) -> InlineKeyboardMarkup:
        """Выбор да/нет"""
        keyboard = [
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="❌ Нет", callback_data=f"{prefix}:no"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def marital_status_choice() -> InlineKeyboardMarkup:
        """Выбор семейного положения"""
        keyboard = [
            [InlineKeyboardButton(text="👤 Холост/Не замужем", callback_data=f"marital:{MaritalStatus.SINGLE.value}")],
            [InlineKeyboardButton(text="💑 Женат/Замужем", callback_data=f"marital:{MaritalStatus.MARRIED.value}")],
            [InlineKeyboardButton(text="💔 Разведен(а)", callback_data=f"marital:{MaritalStatus.DIVORCED.value}")],
            [InlineKeyboardButton(text="🕊 Вдовец/Вдова", callback_data=f"marital:{MaritalStatus.WIDOWED.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def education_choice() -> InlineKeyboardMarkup:
        """Выбор образования"""
        keyboard = [
            [InlineKeyboardButton(text="📚 Среднее", callback_data=f"edu:{Education.SECONDARY.value}")],
            [InlineKeyboardButton(text="🔧 Среднее специальное", callback_data=f"edu:{Education.VOCATIONAL.value}")],
            [InlineKeyboardButton(text="📖 Неполное высшее", callback_data=f"edu:{Education.INCOMPLETE_HIGHER.value}")],
            [InlineKeyboardButton(text="🎓 Высшее", callback_data=f"edu:{Education.HIGHER.value}")],
            [InlineKeyboardButton(text="🎓🎓 Послевузовское", callback_data=f"edu:{Education.POSTGRADUATE.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def housing_status_choice() -> InlineKeyboardMarkup:
        """Выбор статуса жилья"""
        keyboard = [
            [InlineKeyboardButton(text="🏠 Собственное", callback_data=f"house:{HousingStatus.OWN.value}")],
            [InlineKeyboardButton(text="🏦 Собственное (ипотека)", callback_data=f"house:{HousingStatus.OWN_WITH_MORTGAGE.value}")],
            [InlineKeyboardButton(text="🏢 Аренда", callback_data=f"house:{HousingStatus.RENT.value}")],
            [InlineKeyboardButton(text="👨‍👩‍👧 У родственников", callback_data=f"house:{HousingStatus.RELATIVES.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def region_choice() -> InlineKeyboardMarkup:
        """Выбор региона (первая часть)"""
        regions = [
            ("🏙 Ташкент", Region.TASHKENT.value),
            ("🌆 Ташкентская область", Region.TASHKENT_REGION.value),
            ("Андижан", Region.ANDIJAN.value),
            ("Бухара", Region.BUKHARA.value),
            ("Фергана", Region.FERGANA.value),
            ("Джизак", Region.JIZZAKH.value),
            ("Наманган", Region.NAMANGAN.value),
        ]
        
        keyboard = []
        for name, value in regions:
            keyboard.append([InlineKeyboardButton(text=name, callback_data=f"region:{value}")])
        
        keyboard.append([InlineKeyboardButton(text="➡️ Далее", callback_data="region_more")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def region_choice_more() -> InlineKeyboardMarkup:
        """Выбор региона (вторая часть)"""
        regions = [
            ("Навои", Region.NAVOIY.value),
            ("Кашкадарья", Region.QASHQADARYO.value),
            ("Самарканд", Region.SAMARKAND.value),
            ("Сырдарья", Region.SIRDARYO.value),
            ("Сурхандарья", Region.SURXONDARYO.value),
            ("Хорезм", Region.XORAZM.value),
            ("Каракалпакстан", Region.KARAKALPAKSTAN.value),
        ]
        
        keyboard = []
        for name, value in regions:
            keyboard.append([InlineKeyboardButton(text=name, callback_data=f"region:{value}")])
        
        keyboard.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="region_back")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def back_button(callback_data: str = "back") -> InlineKeyboardMarkup:
        """Кнопка назад"""
        keyboard = [
            [InlineKeyboardButton(text="🔙 Назад", callback_data=callback_data)]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def cancel_button() -> InlineKeyboardMarkup:
        """Кнопка отмены"""
        keyboard = [
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def referral_menu(share_url: str) -> InlineKeyboardMarkup:
        """Меню реферальной программы"""
        keyboard = [
            [InlineKeyboardButton(text="📤 Поделиться", url=share_url)],
            [InlineKeyboardButton(text="🔙 В главное меню", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)