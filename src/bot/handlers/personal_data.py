from datetime import datetime

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import Keyboards
from src.bot.states import PersonalDataStates
from src.bot.utils import validate_age, validate_positive_number
from src.core.enums import (
    Education,
    Gender,
    HousingStatus,
    MaritalStatus,
    Region,
)
from src.core.scoring import PersonalData as PersonalDataSchema, ScoringCalculator
from src.db.database import get_db_context
from src.db.models import PersonalData, ReferralRegistration, User

router = Router(name="personal_data")


@router.callback_query(F.data.in_(["personal_data", "fill_personal"]))
async def start_personal_data(callback: types.CallbackQuery, state: FSMContext):
    """Начало заполнения персональных данных"""
    async with get_db_context() as db:
        # Получаем данные пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return
        
        # Получаем персональные данные
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if not personal_data:
            await callback.answer("Ошибка: данные не найдены", show_alert=True)
            return
        
        # Получаем процент заполненности
        schema = PersonalDataSchema(
            age=personal_data.age,
            gender=personal_data.gender,
            work_experience_months=personal_data.work_experience_months,
            address_stability_years=personal_data.address_stability_years,
            housing_status=personal_data.housing_status,
            marital_status=personal_data.marital_status,
            education=personal_data.education,
            closed_loans_count=personal_data.closed_loans_count,
            region=personal_data.region,
            device_type=personal_data.device_type
        )
        completion = ScoringCalculator.get_completion_percentage(schema)
        
        text = f"👤 **Персональные данные**\n\n"
        text += f"Заполнено: {completion}%\n\n"
        text += "Чем больше данных вы укажете, тем выше будет ваш скоринг-балл.\n\n"
        text += "Начнем с возраста. Сколько вам полных лет?"
        
        await callback.message.edit_text(
            text,
            reply_markup=Keyboards.cancel_button(),
            parse_mode="Markdown"
        )
        
        await state.set_state(PersonalDataStates.entering_age)
        await state.update_data(user_id=user.id)
    
    await callback.answer()


@router.message(PersonalDataStates.entering_age)
async def process_age(message: types.Message, state: FSMContext):
    """Обработка возраста"""
    valid, age, error = validate_age(message.text)
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(age=age)
    
    await message.answer(
        "Укажите ваш пол:",
        reply_markup=Keyboards.gender_choice()
    )
    await state.set_state(PersonalDataStates.choosing_gender)


@router.callback_query(PersonalDataStates.choosing_gender, F.data.startswith("gender:"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора пола"""
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    
    await callback.message.edit_text(
        "Сколько месяцев вы работаете на текущем месте работы?\n"
        "(введите 0, если не работаете)",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(PersonalDataStates.entering_work_experience)
    await callback.answer()


@router.message(PersonalDataStates.entering_work_experience)
async def process_work_experience(message: types.Message, state: FSMContext):
    """Обработка стажа работы"""
    valid, months, error = validate_positive_number(message.text, "Стаж")
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(work_experience_months=months)
    
    await message.answer(
        "Сколько лет вы проживаете по текущему адресу?",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(PersonalDataStates.entering_address_stability)


@router.message(PersonalDataStates.entering_address_stability)
async def process_address_stability(message: types.Message, state: FSMContext):
    """Обработка стабильности адреса"""
    valid, years, error = validate_positive_number(message.text, "Количество лет")
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(address_stability_years=years)
    
    await message.answer(
        "Укажите ваш статус жилья:",
        reply_markup=Keyboards.housing_status_choice()
    )
    await state.set_state(PersonalDataStates.choosing_housing_status)


@router.callback_query(PersonalDataStates.choosing_housing_status, F.data.startswith("house:"))
async def process_housing_status(callback: types.CallbackQuery, state: FSMContext):
    """Обработка статуса жилья"""
    housing = callback.data.split(":")[1]
    await state.update_data(housing_status=housing)
    
    await callback.message.edit_text(
        "Укажите ваше семейное положение:",
        reply_markup=Keyboards.marital_status_choice()
    )
    await state.set_state(PersonalDataStates.choosing_marital_status)
    await callback.answer()


@router.callback_query(PersonalDataStates.choosing_marital_status, F.data.startswith("marital:"))
async def process_marital_status(callback: types.CallbackQuery, state: FSMContext):
    """Обработка семейного положения"""
    marital = callback.data.split(":")[1]
    await state.update_data(marital_status=marital)
    
    await callback.message.edit_text(
        "Укажите ваш уровень образования:",
        reply_markup=Keyboards.education_choice()
    )
    await state.set_state(PersonalDataStates.choosing_education)
    await callback.answer()


@router.callback_query(PersonalDataStates.choosing_education, F.data.startswith("edu:"))
async def process_education(callback: types.CallbackQuery, state: FSMContext):
    """Обработка образования"""
    education = callback.data.split(":")[1]
    await state.update_data(education=education)
    
    await callback.message.edit_text(
        "Сколько кредитов вы успешно закрыли?\n"
        "(введите 0, если не было кредитов)",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(PersonalDataStates.entering_closed_loans)
    await callback.answer()


@router.message(PersonalDataStates.entering_closed_loans)
async def process_closed_loans(message: types.Message, state: FSMContext):
    """Обработка количества закрытых кредитов"""
    valid, count, error = validate_positive_number(message.text, "Количество кредитов")
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(closed_loans_count=count)
    
    await message.answer(
        "В каком регионе вы проживаете?",
        reply_markup=Keyboards.region_choice()
    )
    await state.set_state(PersonalDataStates.choosing_region)


@router.callback_query(PersonalDataStates.choosing_region, F.data == "region_more")
async def show_more_regions(callback: types.CallbackQuery):
    """Показать дополнительные регионы"""
    await callback.message.edit_reply_markup(reply_markup=Keyboards.region_choice_more())
    await callback.answer()


@router.callback_query(PersonalDataStates.choosing_region, F.data == "region_back")
async def show_less_regions(callback: types.CallbackQuery):
    """Вернуться к первой части регионов"""
    await callback.message.edit_reply_markup(reply_markup=Keyboards.region_choice())
    await callback.answer()


@router.callback_query(PersonalDataStates.choosing_region, F.data.startswith("region:"))
async def process_region(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора региона"""
    region = callback.data.split(":")[1]
    await state.update_data(region=region)
    
    # Сохраняем все данные
    data = await state.get_data()
    
    async with get_db_context() as db:
        # Обновляем персональные данные
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == data["user_id"])
        )
        personal_data = result.scalar_one_or_none()
        
        if personal_data:
            personal_data.age = data["age"]
            personal_data.gender = Gender(data["gender"])
            personal_data.work_experience_months = data["work_experience_months"]
            personal_data.address_stability_years = data["address_stability_years"]
            personal_data.housing_status = HousingStatus(data["housing_status"])
            personal_data.marital_status = MaritalStatus(data["marital_status"])
            personal_data.education = Education(data["education"])
            personal_data.closed_loans_count = data["closed_loans_count"]
            personal_data.region = Region(data["region"])
            
            # Получаем количество рефералов
            result = await db.execute(
                select(User).where(User.id == data["user_id"])
            )
            user = result.scalar_one_or_none()
            
            # Создаем схему для расчета скоринга
            schema = PersonalDataSchema(
                age=personal_data.age,
                gender=personal_data.gender,
                work_experience_months=personal_data.work_experience_months,
                address_stability_years=personal_data.address_stability_years,
                housing_status=personal_data.housing_status,
                marital_status=personal_data.marital_status,
                education=personal_data.education,
                closed_loans_count=personal_data.closed_loans_count,
                has_other_loans=personal_data.has_other_loans,
                pdn_with_other_loans=personal_data.other_loans_monthly_payment,
                region=personal_data.region,
                device_type=personal_data.device_type,
                referral_count=user.referral_count if user else 0
            )
            
            # Рассчитываем скоринг
            score = ScoringCalculator.calculate_score(schema)
            personal_data.current_score = score
            personal_data.score_updated_at = datetime.utcnow()
            
            # Применяем бонусы за рефералов
            if user and user.referral_count > 0:
                # Находим неприменённые бонусы
                result = await db.execute(
                    select(ReferralRegistration)
                    .where(ReferralRegistration.referrer_id == user.id)
                    .where(ReferralRegistration.bonus_applied == False)
                )
                registrations = result.scalars().all()
                
                for reg in registrations:
                    reg.bonus_applied = True
            
            await db.commit()
            
            # Получаем детализацию скоринга
            breakdown = ScoringCalculator.get_score_breakdown(schema)
            
            # Форматируем сообщение
            message = ScoringCalculator.format_score_message(score, breakdown)
            message += f"\n\n✅ Данные успешно сохранены!"
            
            await callback.message.edit_text(
                message,
                reply_markup=Keyboards.main_menu(),
                parse_mode="Markdown"
            )
    
    await state.clear()
    await callback.answer("Данные сохранены!")