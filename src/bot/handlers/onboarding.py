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
async def cmd_start(message: types.Message, state: FSMContext):
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
                f"С возвращением, {message.from_user.first_name}! 👋\n\n"
                "Выберите действие из меню:",
                reply_markup=Keyboards.main_menu()
            )
            await state.clear()
        else:
            # Новый пользователь - начинаем онбординг
            await state.update_data(referral_code=referral_code)
            
            welcome_text = (
                "Добро пожаловать в KreditScore! 🎉\n\n"
                "Я помогу вам:\n"
                "• Рассчитать показатель долговой нагрузки\n"
                "• Оценить вероятность одобрения кредита\n"
                "• Подобрать лучшие предложения от банков\n\n"
                "Для начала мне нужен ваш номер телефона."
            )
            
            await message.answer(
                welcome_text,
                reply_markup=Keyboards.phone_request()
            )
            await state.set_state(OnboardingStates.waiting_for_phone)


@router.message(OnboardingStates.waiting_for_phone, F.contact)
async def process_phone(message: types.Message, state: FSMContext):
    """Обработка полученного контакта"""
    contact = message.contact
    
    # Проверяем, что это контакт самого пользователя
    if contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Пожалуйста, поделитесь своим номером телефона.",
            reply_markup=Keyboards.phone_request()
        )
        return
    
    # Валидация номера
    phone = validate_phone_number(contact.phone_number)
    if not phone:
        await message.answer(
            "⚠️ Некорректный номер телефона. Попробуйте еще раз.",
            reply_markup=Keyboards.phone_request()
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
        "Отлично! Теперь выберите язык интерфейса:",
        reply_markup=Keyboards.remove()
    )
    
    # Предлагаем выбрать язык
    await message.answer(
        "Выберите язык / Tilni tanlang:",
        reply_markup=Keyboards.language_choice()
    )
    await state.set_state(OnboardingStates.waiting_for_language)


@router.message(OnboardingStates.waiting_for_phone)
async def process_phone_text(message: types.Message):
    """Обработка текстового сообщения вместо контакта"""
    await message.answer(
        "Пожалуйста, используйте кнопку для отправки номера телефона.",
        reply_markup=Keyboards.phone_request()
    )


@router.callback_query(OnboardingStates.waiting_for_language, F.data.startswith("lang:"))
async def process_language(callback: types.CallbackQuery, state: FSMContext):
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
    
    # Завершаем онбординг
    await callback.message.edit_text(
        "✅ Регистрация завершена!\n\n"
        "Теперь вы можете:\n"
        "• Подать заявку на кредит\n"
        "• Рассчитать долговую нагрузку\n"
        "• Узнать свой кредитный рейтинг\n\n"
        "Выберите действие из меню:",
        reply_markup=Keyboards.main_menu()
    )
    
    await state.clear()
    await callback.answer()


@router.message(Command("menu"))
async def cmd_menu(message: types.Message, state: FSMContext):
    """Команда для отображения главного меню"""
    async with get_db_context() as db:
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                "Вы еще не зарегистрированы. Используйте /start для начала."
            )
            return
    
    await message.answer(
        "Главное меню:",
        reply_markup=Keyboards.main_menu()
    )
    await state.clear()


@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery, state: FSMContext):
    """Показать главное меню"""
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=Keyboards.main_menu()
    )
    await state.clear()
    await callback.answer()