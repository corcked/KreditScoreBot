from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import Keyboards
from src.bot.states import OnboardingStates
from src.bot.utils import detect_device_type, validate_phone_number
from src.core.referral import ReferralSystem
from src.db.database import get_db_context
from src.db.models import PersonalData, ReferralRegistration, User

router = Router(name="onboarding")


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext, _: callable):
    """Обработка команды /start"""
    user_id = message.from_user.id
    
    # Проверяем, есть ли реферальный код
    referral_code = None
    if message.text and len(message.text.split()) > 1:
        start_param = message.text.split()[1]
        referral_code = ReferralSystem.parse_referral_code(start_param)
    
    async with get_db_context() as db:
        # Проверяем, существует ли пользователь
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Пользователь уже зарегистрирован
            await message.answer(
                f"{_('Welcome!')} {message.from_user.first_name}! 👋\n\n"
                f"{_('Main menu')}:",
                reply_markup=Keyboards.main_menu(_)
            )
            await state.clear()
        else:
            # Новый пользователь - начинаем онбординг
            await state.update_data(referral_code=referral_code)
            
            welcome_text = (
                f"{_('Welcome! I\'m KreditScore Bot.')} 🎉\n\n"
                f"{_('I\'ll help you:')}\n"
                f"• {_('Calculate debt burden indicator')}\n"
                f"• {_('Get credit score')}\n"
                f"• {_('Apply for a loan')}\n\n"
                f"{_('Share your phone number to continue')}"
            )
            
            await message.answer(
                welcome_text,
                reply_markup=Keyboards.phone_request(_)
            )
            await state.set_state(OnboardingStates.waiting_for_phone)


@router.message(OnboardingStates.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext, _: callable):
    """Обработка полученного контакта"""
    contact = message.contact
    
    # Проверяем, что это контакт самого пользователя
    if contact.user_id != message.from_user.id:
        await message.answer(
            f"⚠️ {_('Share your phone number to continue')}",
            reply_markup=Keyboards.phone_request(_)
        )
        return
    
    # Валидация номера
    phone = validate_phone_number(contact.phone_number)
    if not phone:
        await message.answer(
            f"⚠️ {_('Incorrect phone number. Try again.')}",
            reply_markup=Keyboards.phone_request(_)
        )
        return
    
    # Сохраняем данные
    state_data = await state.get_data()
    referral_code = state_data.get("referral_code")
    
    async with get_db_context() as db:
        # Создаем пользователя
        user = User(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            phone_number=phone,
            referral_code=ReferralSystem.generate_referral_code(message.from_user.id),
            language_code=message.from_user.language_code or "ru"
        )
        
        # Сначала добавляем и сохраняем пользователя
        db.add(user)
        await db.flush()  # Flush чтобы получить user.id
        
        # Обрабатываем реферальную регистрацию
        if referral_code and ReferralSystem.validate_referral_code(referral_code):
            # Находим реферера по коду
            result = await db.execute(
                select(User).where(User.referral_code == referral_code)
            )
            referrer = result.scalar_one_or_none()
            
            if referrer and referrer.telegram_id != message.from_user.id:
                # Обновляем связь с реферером
                user.referred_by_id = referrer.id
                
                # Создаем запись о реферальной регистрации
                registration = ReferralRegistration(
                    referrer_id=referrer.id,
                    referred_user_id=user.id,
                    bonus_points=20
                )
                db.add(registration)
                
                # Увеличиваем счетчик рефералов
                referrer.referral_count += 1
        
        # Теперь создаем персональные данные с правильным user_id
        personal_data = PersonalData(
            user_id=user.id,
            device_type=detect_device_type(message.from_user)
        )
        
        db.add(personal_data)
        await db.commit()
    
    # Убираем клавиатуру
    await message.answer(
        f"✅ {_('Welcome!')}",
        reply_markup=Keyboards.remove()
    )
    
    # Предлагаем выбрать язык
    await message.answer(
        f"{_('Choose language')} / Tilni tanlang:",
        reply_markup=Keyboards.language_choice(_)
    )
    await state.set_state(OnboardingStates.waiting_for_language)


@router.message(OnboardingStates.waiting_for_phone)
async def process_phone_text(message: types.Message, _: callable):
    """Обработка текстового сообщения вместо контакта"""
    await message.answer(
        f"{_('Share your phone number to continue')}",
        reply_markup=Keyboards.phone_request(_)
    )


@router.callback_query(OnboardingStates.waiting_for_language, F.data.startswith("lang:"))
async def process_language(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Обработка выбора языка"""
    language = callback.data.split(":")[1]
    
    async with get_db_context() as db:
        # Обновляем язык пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            user.language_code = language
            await db.commit()
    
    # Обновляем функцию перевода для нового языка
    from src.bot.utils.i18n import simple_gettext
    new_translate = lambda msg: simple_gettext(language, msg)
    
    # Завершаем онбординг
    await callback.message.edit_text(
        f"✅ {new_translate('Welcome!')}\n\n"
        f"{new_translate('I\'ll help you:')}\n"
        f"• {new_translate('Apply for a loan')}\n"
        f"• {new_translate('Calculate debt burden indicator')}\n"
        f"• {new_translate('Get credit score')}\n\n"
        f"{new_translate('Main menu')}:",
        reply_markup=Keyboards.main_menu(new_translate)
    )
    
    await state.clear()
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext, _: callable):
    """Команда для отображения главного меню"""
    async with get_db_context() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                _('You are not registered. Use /start to begin.')
            )
            return
    
    await message.answer(
        f"{_('Main menu')}:",
        reply_markup=Keyboards.main_menu(_)
    )
    await state.clear()


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Показать главное меню"""
    await callback.message.edit_text(
        f"{_('Main menu')}:",
        reply_markup=Keyboards.main_menu(_)
    )
    await state.clear()
    await callback.answer()