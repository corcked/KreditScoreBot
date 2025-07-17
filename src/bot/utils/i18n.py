import gettext
import os
from pathlib import Path
from typing import Dict, Optional

from aiogram import types

# Поддерживаемые языки
SUPPORTED_LANGUAGES = {
    "ru": "Русский",
    "uz": "O'zbek"
}

# Путь к файлам переводов
LOCALES_DIR = Path(__file__).parent.parent / "i18n"

# Хранилище объектов переводов
_translations: Dict[str, gettext.GNUTranslations] = {}


def load_translations():
    """Загрузка всех доступных переводов"""
    for lang_code in SUPPORTED_LANGUAGES:
        po_file = LOCALES_DIR / f"{lang_code}.po"
        mo_file = LOCALES_DIR / f"{lang_code}.mo"
        
        # Компилируем .po в .mo если необходимо
        if po_file.exists():
            # В продакшене обычно используются предкомпилированные .mo файлы
            # Здесь мы будем использовать .po напрямую через polib
            try:
                with open(po_file, 'rb') as f:
                    _translations[lang_code] = gettext.GNUTranslations(f)
            except Exception:
                # Если не получилось загрузить, используем NullTranslations
                _translations[lang_code] = gettext.NullTranslations()


def get_user_language(user: Optional[types.User] = None, 
                     user_language: Optional[str] = None) -> str:
    """
    Определение языка пользователя
    
    Args:
        user: Объект пользователя Telegram
        user_language: Сохраненный язык пользователя из БД
        
    Returns:
        Код языка
    """
    # Приоритет: сохраненный язык > язык из Telegram > русский по умолчанию
    if user_language and user_language in SUPPORTED_LANGUAGES:
        return user_language
    
    if user and user.language_code:
        # Telegram может отдавать язык в формате "ru-RU", берем первую часть
        lang_code = user.language_code.split('-')[0].lower()
        if lang_code in SUPPORTED_LANGUAGES:
            return lang_code
    
    return "ru"  # Русский по умолчанию


def get_translator(lang_code: str) -> gettext.GNUTranslations:
    """
    Получение объекта переводчика для языка
    
    Args:
        lang_code: Код языка
        
    Returns:
        Объект переводчика
    """
    if lang_code not in _translations:
        # Если перевод не найден, используем пустой (вернет оригинальный текст)
        return gettext.NullTranslations()
    
    return _translations[lang_code]


class I18nContext:
    """Контекст для хранения текущего языка пользователя"""
    
    def __init__(self, lang_code: str = "ru"):
        self.lang_code = lang_code
        self._translator = get_translator(lang_code)
    
    def _(self, message: str) -> str:
        """Функция перевода"""
        return self._translator.gettext(message)
    
    def ngettext(self, singular: str, plural: str, n: int) -> str:
        """Функция перевода с множественными формами"""
        return self._translator.ngettext(singular, plural, n)
    
    def set_language(self, lang_code: str):
        """Смена языка"""
        self.lang_code = lang_code
        self._translator = get_translator(lang_code)


# Временное решение для работы без .po файлов
# В реальном приложении эти тексты будут в .po файлах
TRANSLATIONS = {
    "ru": {
        # Общие
        "Back": "Назад",
        "Cancel": "Отмена",
        "Main menu": "Главное меню",
        "Settings": "Настройки",
        "Language": "Язык",
        "Choose language": "Выберите язык",
        
        # Приветствие
        "Welcome! I'm KreditScore Bot.": "Добро пожаловать! Я бот KreditScore.",
        "I'll help you:": "Я помогу вам:",
        "Calculate debt burden indicator": "Рассчитать показатель долговой нагрузки",
        "Get credit score": "Получить кредитный скоринг",
        "Apply for a loan": "Подать заявку на кредит",
        "Share your phone number to continue": "Поделитесь номером телефона для продолжения",
        "Share phone number": "Поделиться номером",
        
        # Главное меню
        "New application": "Новая заявка",
        "My applications": "Мои заявки",
        "My indicators": "Мои показатели",
        "Personal data": "Личные данные",
        "Referral program": "Реферальная программа",
        
        # Кредиты
        "Choose loan type": "Выберите тип кредита",
        "Car loan": "Автокредит",
        "Microloan": "Микрозайм",
        "Up to": "До",
        "Rate": "Ставка",
        "Term": "Срок",
        "months": "мес",
        "years": "лет",
        
        # ПДН и скоринг
        "Your financial indicators": "Ваши финансовые показатели",
        "Debt burden indicator": "Показатель долговой нагрузки",
        "Excellent indicator!": "Отличный показатель!",
        "Acceptable indicator": "Приемлемый показатель",
        "High debt burden": "Высокая долговая нагрузка",
        "Banks may approve the loan": "Банки могут одобрить кредит",
        "Banks do not issue loans with DTI > 50%": "При ПДН > 50% банки не выдают кредиты",
        "Credit scoring": "Кредитный скоринг",
        "Your score": "Ваш балл",
        "Profile completion": "Профиль заполнен на",
        "Fill in all data to increase score": "Заполните все данные для увеличения балла",
        
        # Персональные данные
        "Fill personal data": "Заполнить личные данные",
        "Age": "Возраст",
        "Gender": "Пол",
        "Male": "Мужской",
        "Female": "Женский",
        "Marital status": "Семейное положение",
        "Single": "Холост/Не замужем",
        "Married": "Женат/Замужем",
        "Divorced": "Разведен(а)",
        "Widowed": "Вдовец/Вдова",
        "Education": "Образование",
        "Secondary": "Среднее",
        "Vocational": "Среднее специальное",
        "Incomplete higher": "Неполное высшее",
        "Higher": "Высшее",
        "Postgraduate": "Послевузовское",
        "Housing status": "Статус жилья",
        "Own": "Собственное",
        "Own with mortgage": "Собственное (ипотека)",
        "Rent": "Аренда",
        "With relatives": "У родственников",
        "Region": "Регион",
        "Work experience (months)": "Стаж работы (месяцев)",
        "Years at current address": "Лет по текущему адресу",
        "Do you have other loans?": "Есть ли у вас другие кредиты?",
        "Yes": "Да",
        "No": "Нет",
        "Number of closed loans": "Количество закрытых кредитов",
        
        # Ошибки
        "Incorrect phone number. Try again.": "Некорректный номер телефона. Попробуйте еще раз.",
        "You are not registered. Use /start to begin.": "Вы еще не зарегистрированы. Используйте /start для начала.",
        "Error: user not found": "Ошибка: пользователь не найден",
        "Error: data not found": "Ошибка: данные не найдены",
        "Active application not found": "Активная заявка не найдена",
        "Enter correct amount (numbers only)": "Введите корректную сумму (только цифры)",
        "Amount must be positive": "Сумма должна быть положительной",
        "Maximum amount": "Максимальная сумма",
        
        # Статусы
        "New": "Новая",
        "Sent to bank": "Отправлена в банк",
        "Archived": "В архиве",
        
        # Подтверждения
        "Application created successfully!": "Заявка успешно создана!",
        "Personal data saved!": "Личные данные сохранены!",
        "Language changed successfully": "Язык успешно изменен",
        
        # Реферальная программа - дополнительные
        "Share this link with friends. When they register using your link, you will automatically receive bonus points!": "Поделитесь этой ссылкой с друзьями. Когда они зарегистрируются в боте по вашей ссылке, вы автоматически получите бонусные баллы!",
        "discover your credit rating!": "узнай свой кредитный рейтинг!",
        "Instant debt burden calculation": "Мгновенный расчет долговой нагрузки",
        "Credit approval probability assessment": "Оценка вероятности одобрения кредита",
        "Best offers from banks": "Лучшие предложения от банков",
        "Start now": "Начни прямо сейчас",
    },
    "uz": {
        # Общие
        "Back": "Orqaga",
        "Cancel": "Bekor qilish",
        "Main menu": "Asosiy menyu",
        "Settings": "Sozlamalar",
        "Language": "Til",
        "Choose language": "Tilni tanlang",
        
        # Приветствие
        "Welcome! I'm KreditScore Bot.": "Xush kelibsiz! Men KreditScore botiman.",
        "I'll help you:": "Men sizga yordam beraman:",
        "Calculate debt burden indicator": "Qarz yukini hisoblash",
        "Get credit score": "Kredit skoringni olish",
        "Apply for a loan": "Kredit uchun ariza berish",
        "Share your phone number to continue": "Davom etish uchun telefon raqamingizni ulashing",
        "Share phone number": "Telefon raqamini ulashish",
        
        # Главное меню
        "New application": "Yangi ariza",
        "My applications": "Mening arizalarim",
        "My indicators": "Mening ko'rsatkichlarim",
        "Personal data": "Shaxsiy ma'lumotlar",
        "Referral program": "Referal dasturi",
        
        # Кредиты
        "Choose loan type": "Kredit turini tanlang",
        "Car loan": "Avtokredit",
        "Microloan": "Mikroqarz",
        "Up to": "gacha",
        "Rate": "Stavka",
        "Term": "Muddat",
        "months": "oy",
        "years": "yil",
        
        # ПДН и скоринг
        "Your financial indicators": "Sizning moliyaviy ko'rsatkichlaringiz",
        "Debt burden indicator": "Qarz yuki ko'rsatkichi",
        "Excellent indicator!": "A'lo ko'rsatkich!",
        "Acceptable indicator": "Qoniqarli ko'rsatkich",
        "High debt burden": "Yuqori qarz yuki",
        "Banks may approve the loan": "Banklar kreditni tasdiqlashi mumkin",
        "Banks do not issue loans with DTI > 50%": "QYK > 50% bo'lsa banklar kredit bermaydi",
        "Credit scoring": "Kredit skoring",
        "Your score": "Sizning balingiz",
        "Profile completion": "Profil to'ldirilgan",
        "Fill in all data to increase score": "Balni oshirish uchun barcha ma'lumotlarni to'ldiring",
        
        # Персональные данные
        "Fill personal data": "Shaxsiy ma'lumotlarni to'ldirish",
        "Age": "Yosh",
        "Gender": "Jins",
        "Male": "Erkak",
        "Female": "Ayol",
        "Marital status": "Oilaviy holat",
        "Single": "Turmush qurmagan",
        "Married": "Turmush qurgan",
        "Divorced": "Ajrashgan",
        "Widowed": "Beva",
        "Education": "Ta'lim",
        "Secondary": "O'rta",
        "Vocational": "O'rta maxsus",
        "Incomplete higher": "Tugallanmagan oliy",
        "Higher": "Oliy",
        "Postgraduate": "Oliy ta'limdan keyingi",
        "Housing status": "Uy-joy holati",
        "Own": "Shaxsiy",
        "Own with mortgage": "Shaxsiy (ipoteka)",
        "Rent": "Ijara",
        "With relatives": "Qarindoshlar bilan",
        "Region": "Viloyat",
        "Work experience (months)": "Ish staji (oy)",
        "Years at current address": "Joriy manzilda (yil)",
        "Do you have other loans?": "Boshqa kreditlaringiz bormi?",
        "Yes": "Ha",
        "No": "Yo'q",
        "Number of closed loans": "Yopilgan kreditlar soni",
        
        # Ошибки
        "Incorrect phone number. Try again.": "Noto'g'ri telefon raqami. Qayta urinib ko'ring.",
        "You are not registered. Use /start to begin.": "Siz ro'yxatdan o'tmagansiz. Boshlash uchun /start dan foydalaning.",
        "Error: user not found": "Xato: foydalanuvchi topilmadi",
        "Error: data not found": "Xato: ma'lumotlar topilmadi",
        "Active application not found": "Faol ariza topilmadi",
        "Enter correct amount (numbers only)": "To'g'ri summani kiriting (faqat raqamlar)",
        "Amount must be positive": "Summa musbat bo'lishi kerak",
        "Maximum amount": "Maksimal summa",
        
        # Статусы
        "New": "Yangi",
        "Sent to bank": "Bankka yuborildi",
        "Archived": "Arxivda",
        
        # Подтверждения
        "Application created successfully!": "Ariza muvaffaqiyatli yaratildi!",
        "Personal data saved!": "Shaxsiy ma'lumotlar saqlandi!",
        "Language changed successfully": "Til muvaffaqiyatli o'zgartirildi",
        
        # Реферальная программа - дополнительные
        "Share this link with friends. When they register using your link, you will automatically receive bonus points!": "Bu havolani do'stlaringiz bilan ulashing. Ular sizning havolangiz orqali ro'yxatdan o'tganlarida, siz avtomatik ravishda bonus ballar olasiz!",
        "discover your credit rating!": "kredit reytingingizni bilib oling!",
        "Instant debt burden calculation": "Qarz yukini tezkor hisoblash",
        "Credit approval probability assessment": "Kredit tasdiqlash ehtimolini baholash",
        "Best offers from banks": "Banklarning eng yaxshi takliflari",
        "Start now": "Hoziroq boshlang",
    }
}


def simple_gettext(lang_code: str, message: str) -> str:
    """
    Простая функция перевода без использования .po файлов
    Временное решение для демонстрации
    """
    if lang_code in TRANSLATIONS and message in TRANSLATIONS[lang_code]:
        return TRANSLATIONS[lang_code][message]
    return message