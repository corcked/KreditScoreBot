from typing import Callable, List, Optional

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
    """Клавиатуры для бота с поддержкой локализации"""

    @staticmethod
    def phone_request(_: Callable[[str], str]) -> ReplyKeyboardMarkup:
        """Клавиатура для запроса номера телефона"""
        keyboard = [
            [KeyboardButton(text=f"📱 {_('Share phone number')}", request_contact=True)]
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
    def language_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор языка"""
        keyboard = [
            [
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
                InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="lang:uz"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def main_menu(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Главное меню"""
        keyboard = [
            [InlineKeyboardButton(text=f"💳 {_('New application')}", callback_data="new_loan")],
            [InlineKeyboardButton(text=f"📋 {_('My applications')}", callback_data="my_applications")],
            [InlineKeyboardButton(text=f"📊 {_('My indicators')}", callback_data="my_score")],
            [InlineKeyboardButton(text=f"👤 {_('Personal data')}", callback_data="personal_data")],
            [InlineKeyboardButton(text=f"🎁 {_('Referral program')}", callback_data="referral")],
            [InlineKeyboardButton(text=f"⚙️ {_('Settings')}", callback_data="settings")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def loan_type_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор типа кредита"""
        keyboard = [
            [InlineKeyboardButton(text=f"🚗 {_('Car loan')}", callback_data=f"loan_type:{LoanType.CARLOAN.value}")],
            [InlineKeyboardButton(text=f"💰 {_('Microloan')}", callback_data=f"loan_type:{LoanType.MICROLOAN.value}")],
            [InlineKeyboardButton(text=f"❌ {_('Cancel')}", callback_data="cancel")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def car_condition_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор состояния автомобиля"""
        keyboard = [
            [InlineKeyboardButton(text=f"✨ {_('New')}", callback_data=f"car:{CarCondition.NEW.value}")],
            [InlineKeyboardButton(text=f"🚙 {_('Used')}", callback_data=f"car:{CarCondition.USED.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def receive_method_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор способа получения"""
        keyboard = [
            [InlineKeyboardButton(text=f"💳 {_('To card')}", callback_data=f"receive:{ReceiveMethod.CARD.value}")],
            [InlineKeyboardButton(text=f"💵 {_('Cash')}", callback_data=f"receive:{ReceiveMethod.CASH.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def skip_other_payments(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Пропустить ввод других платежей"""
        keyboard = [
            [InlineKeyboardButton(text=f"➡️ {_('Skip')}", callback_data="skip_other_payments")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def confirm_application(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Подтверждение заявки"""
        keyboard = [
            [
                InlineKeyboardButton(text=f"✅ {_('Confirm')}", callback_data="confirm_app"),
                InlineKeyboardButton(text=f"❌ {_('Cancel')}", callback_data="cancel_app"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def application_actions(_: Callable[[str], str], can_send: bool = True) -> InlineKeyboardMarkup:
        """Действия с заявкой"""
        keyboard = []
        
        if can_send:
            keyboard.append([InlineKeyboardButton(text=f"🏦 {_('Send to bank')}", callback_data="send_to_bank")])
        
        keyboard.extend([
            [InlineKeyboardButton(text=f"👤 {_('Fill personal data')}", callback_data="fill_personal")],
            [InlineKeyboardButton(text=f"🔙 {_('Main menu')}", callback_data="main_menu")],
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def gender_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор пола"""
        keyboard = [
            [
                InlineKeyboardButton(text=f"👨 {_('Male')}", callback_data=f"gender:{Gender.MALE.value}"),
                InlineKeyboardButton(text=f"👩 {_('Female')}", callback_data=f"gender:{Gender.FEMALE.value}"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def yes_no_choice(_: Callable[[str], str], prefix: str) -> InlineKeyboardMarkup:
        """Выбор да/нет"""
        keyboard = [
            [
                InlineKeyboardButton(text=f"✅ {_('Yes')}", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text=f"❌ {_('No')}", callback_data=f"{prefix}:no"),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def marital_status_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор семейного положения"""
        keyboard = [
            [InlineKeyboardButton(text=f"👤 {_('Single')}", callback_data=f"marital:{MaritalStatus.SINGLE.value}")],
            [InlineKeyboardButton(text=f"💑 {_('Married')}", callback_data=f"marital:{MaritalStatus.MARRIED.value}")],
            [InlineKeyboardButton(text=f"💔 {_('Divorced')}", callback_data=f"marital:{MaritalStatus.DIVORCED.value}")],
            [InlineKeyboardButton(text=f"🕊 {_('Widowed')}", callback_data=f"marital:{MaritalStatus.WIDOWED.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def education_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор образования"""
        keyboard = [
            [InlineKeyboardButton(text=f"📚 {_('Secondary')}", callback_data=f"edu:{Education.SECONDARY.value}")],
            [InlineKeyboardButton(text=f"🔧 {_('Vocational')}", callback_data=f"edu:{Education.VOCATIONAL.value}")],
            [InlineKeyboardButton(text=f"📖 {_('Incomplete higher')}", callback_data=f"edu:{Education.INCOMPLETE_HIGHER.value}")],
            [InlineKeyboardButton(text=f"🎓 {_('Higher')}", callback_data=f"edu:{Education.HIGHER.value}")],
            [InlineKeyboardButton(text=f"🎓🎓 {_('Postgraduate')}", callback_data=f"edu:{Education.POSTGRADUATE.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def housing_status_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор статуса жилья"""
        keyboard = [
            [InlineKeyboardButton(text=f"🏠 {_('Own')}", callback_data=f"house:{HousingStatus.OWN.value}")],
            [InlineKeyboardButton(text=f"🏦 {_('Own with mortgage')}", callback_data=f"house:{HousingStatus.OWN_WITH_MORTGAGE.value}")],
            [InlineKeyboardButton(text=f"🏢 {_('Rent')}", callback_data=f"house:{HousingStatus.RENT.value}")],
            [InlineKeyboardButton(text=f"👨‍👩‍👧 {_('With relatives')}", callback_data=f"house:{HousingStatus.RELATIVES.value}")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def region_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Выбор региона (первая часть)"""
        regions = [
            (f"🏙 {_('Tashkent')}", Region.TASHKENT.value),
            (f"🌆 {_('Tashkent region')}", Region.TASHKENT_REGION.value),
            ("Андижан", Region.ANDIJAN.value),
            ("Бухара", Region.BUKHARA.value),
            ("Фергана", Region.FERGANA.value),
            ("Джизак", Region.JIZZAKH.value),
            ("Наманган", Region.NAMANGAN.value),
        ]
        
        keyboard = []
        for name, value in regions:
            keyboard.append([InlineKeyboardButton(text=name, callback_data=f"region:{value}")])
        
        keyboard.append([InlineKeyboardButton(text=f"➡️ {_('Next')}", callback_data="region_more")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def region_choice_more(_: Callable[[str], str]) -> InlineKeyboardMarkup:
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
        
        keyboard.append([InlineKeyboardButton(text=f"⬅️ {_('Back')}", callback_data="region_back")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def back_button(_: Callable[[str], str], callback_data: str = "back") -> InlineKeyboardMarkup:
        """Кнопка назад"""
        keyboard = [
            [InlineKeyboardButton(text=f"🔙 {_('Back')}", callback_data=callback_data)]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def cancel_button(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Кнопка отмены"""
        keyboard = [
            [InlineKeyboardButton(text=f"❌ {_('Cancel')}", callback_data="cancel")]
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def referral_menu(_: Callable[[str], str], share_url: str) -> InlineKeyboardMarkup:
        """Меню реферальной программы"""
        keyboard = [
            [InlineKeyboardButton(text=f"📤 {_('Share')}", url=share_url)],
            [InlineKeyboardButton(text=f"🔙 {_('Main menu')}", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    @staticmethod
    def settings_menu(_: Callable[[str], str]) -> InlineKeyboardMarkup:
        """Меню настроек"""
        keyboard = [
            [InlineKeyboardButton(text=f"🌐 {_('Language')}", callback_data="change_language")],
            [InlineKeyboardButton(text=f"🔙 {_('Main menu')}", callback_data="main_menu")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=keyboard)