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
    DeviceType,
)
from src.core.scoring import PersonalData as PersonalDataSchema, ScoringCalculator
from src.core.field_protection import FieldProtectionManager
from src.db.database import get_db_context
from src.db.models import PersonalData, ReferralRegistration, User

router = Router(name="personal_data")


@router.callback_query(F.data.in_(["personal_data", "fill_personal"]))
async def start_personal_data(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Начало заполнения персональных данных"""
    async with get_db_context() as db:
        # Получаем данные пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer(_('Error: user not found'), show_alert=True)
            return
        
        # Получаем персональные данные
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if not personal_data:
            await callback.answer(_('Error: data not found'), show_alert=True)
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
        
        text = f"👤 **{_('Personal data')}**\n\n"
        text += f"{_('Profile completion')}: {completion}%\n\n"
        text += f"{_('Fill in all data to increase score')}\n\n"
        text += _('Enter your age')
        
        await callback.message.edit_text(
            text,
            reply_markup=Keyboards.cancel_button(_),
            parse_mode="Markdown"
        )
        
        await state.set_state(PersonalDataStates.entering_age)
        await state.update_data(user_id=user.id)
    
    await callback.answer()


@router.message(PersonalDataStates.entering_age)
async def process_age(message: types.Message, state: FSMContext, _: callable):
    """Обработка возраста"""
    valid, age, error = validate_age(message.text, _)
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button(_))
        return
    
    await state.update_data(age=age)
    
    await message.answer(
        _('Choose your gender'),
        reply_markup=Keyboards.gender_choice(_)
    )
    await state.set_state(PersonalDataStates.choosing_gender)


@router.callback_query(PersonalDataStates.choosing_gender, F.data.startswith("gender:"))
async def process_gender(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Обработка выбора пола"""
    gender = callback.data.split(":")[1]
    await state.update_data(gender=gender)
    
    await callback.message.edit_text(
        _('Enter work experience in months'),
        reply_markup=Keyboards.cancel_button(_)
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


@router.callback_query(F.data == "edit_personal_data")
async def show_personal_data_menu(callback: types.CallbackQuery, _: callable):
    """Показать меню редактирования персональных данных"""
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text(
                f"❌ {_('User not found')}",
                reply_markup=Keyboards.back_to_menu(_)
            )
            return
        
        # Получаем персональные данные пользователя
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if not personal_data:
            await callback.message.edit_text(
                f"❌ {_('Personal data not found')}",
                reply_markup=Keyboards.back_to_menu(_)
            )
            return
        
        # Получаем статус полей
        field_status = FieldProtectionManager.get_field_status(personal_data)
        
        # Показываем меню с учетом защищенных полей
        await show_data_menu_with_protection(callback, field_status, personal_data, _)


async def show_data_menu_with_protection(
    callback: types.CallbackQuery, 
    field_status: dict, 
    personal_data: PersonalData,
    _: callable
):
    """Показать меню данных с учетом защиты полей"""
    
    message = f"👤 **{_('Personal Data')}**\n\n"
    
    # Разделяем поля на группы
    protected_fields = []
    editable_fields = []
    filled_fields = []
    
    for field_name, status in field_status.items():
        if status['is_protected']:
            protected_fields.append((field_name, status))
        elif status['is_filled']:
            filled_fields.append((field_name, status))
        else:
            editable_fields.append((field_name, status))
    
    # Показываем заполненные данные
    if filled_fields or protected_fields:
        message += f"📋 **{_('Current Data')}:**\n"
        
        for field_name, status in filled_fields + protected_fields:
            value = format_field_value(status['current_value'], field_name, _)
            icon = "🔒" if status['is_protected'] else "✅"
            message += f"{icon} {_(status['display_name'])}: {value}\n"
    
    # Показываем доступные для редактирования
    if editable_fields:
        message += f"\n✏️ **{_('Available for editing')}:**\n"
        for field_name, status in editable_fields:
            if not status['is_filled']:
                message += f"📝 {_(status['display_name'])}: {_('Not filled')}\n"
    
    # Информация о защищенных полях
    if protected_fields:
        message += f"\n🔒 **{_('Protected fields')}:** {len(protected_fields)}\n"
        message += f"💡 {_('These fields cannot be changed as they affect your credit score')}\n"
    
    # Добавляем информацию о текущем скоринге
    if personal_data.current_score:
        message += f"\n📊 **{_('Current score')}:** {personal_data.current_score} {_('points')}\n"
    
    await callback.message.edit_text(
        message,
        reply_markup=Keyboards.personal_data_menu_protected(field_status, _),
        parse_mode="Markdown"
    )


def format_field_value(value: any, field_name: str, _: callable) -> str:
    """Форматирует значение поля для отображения"""
    if value is None:
        return _("Not filled")
    
    # Специальное форматирование для разных типов полей
    if field_name == 'gender':
        return _("Male") if value == Gender.MALE else _("Female")
    elif field_name == 'monthly_income':
        return f"{value:,.0f} {_('som')}".replace(",", " ")
    elif field_name == 'has_other_loans':
        return _("Yes") if value else _("No")
    elif field_name in ['work_experience_months', 'address_stability_years']:
        if field_name == 'work_experience_months':
            return f"{value} {_('months')}"
        else:
            return f"{value} {_('years')}"
    elif field_name == 'housing_status':
        housing_map = {
            HousingStatus.OWN: _("Own property"),
            HousingStatus.OWN_WITH_MORTGAGE: _("Own with mortgage"),
            HousingStatus.RENT: _("Rent"),
            HousingStatus.RELATIVES: _("With relatives")
        }
        return housing_map.get(value, str(value))
    elif field_name == 'marital_status':
        marital_map = {
            MaritalStatus.SINGLE: _("Single"),
            MaritalStatus.MARRIED: _("Married"),
            MaritalStatus.DIVORCED: _("Divorced"),
            MaritalStatus.WIDOWED: _("Widowed")
        }
        return marital_map.get(value, str(value))
    elif field_name == 'education':
        education_map = {
            Education.SECONDARY: _("Secondary"),
            Education.SPECIALIZED_SECONDARY: _("Specialized secondary"),
            Education.INCOMPLETE_HIGHER: _("Incomplete higher"),
            Education.HIGHER: _("Higher"),
            Education.POSTGRADUATE: _("Postgraduate")
        }
        return education_map.get(value, str(value))
    elif field_name == 'region':
        # Для региона просто возвращаем значение enum
        return str(value.value).replace('_', ' ')
    elif field_name == 'device_type':
        device_map = {
            DeviceType.APPLE: _("Apple"),
            DeviceType.ANDROID: _("Android"),
            DeviceType.OTHER: _("Other")
        }
        return device_map.get(value, str(value))
    
    return str(value)


@router.callback_query(F.data == "explain_protection")
async def explain_field_protection(callback: types.CallbackQuery, _: callable):
    """Объяснить систему защиты полей"""
    
    message = f"🔒 **{_('Field Protection System')}**\n\n"
    
    message += f"**{_('Why are some fields protected?')}**\n"
    message += f"• {_('Filled fields affect your credit score')}\n"
    message += f"• {_('This prevents score manipulation')}\n"
    message += f"• {_('Ensures assessment reliability')}\n\n"
    
    message += f"**{_('What you can always edit:')}**\n"
    message += f"💰 {_('Monthly income')}\n"
    message += f"🏦 {_('Information about other loans')}\n\n"
    
    message += f"**{_('What gets protected:')}**\n"
    message += f"👤 {_('Personal information (age, gender)')}\n"
    message += f"🏠 {_('Housing and family status')}\n"
    message += f"🎓 {_('Education and work experience')}\n"
    message += f"📍 {_('Location and device type')}\n\n"
    
    message += f"💡 {_('Tip: Fill all fields carefully before first scoring calculation!')}"
    
    await callback.message.edit_text(
        message,
        reply_markup=Keyboards.back_to_personal_data(_),
        parse_mode="Markdown"
    )


@router.callback_query(F.data == "view_protected_data")
async def view_protected_data(callback: types.CallbackQuery, _: callable):
    """Показать защищенные данные"""
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer(_("User not found"))
            return
        
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if not personal_data:
            await callback.answer(_("Data not found"))
            return
        
        field_status = FieldProtectionManager.get_field_status(personal_data)
        protected_fields = [
            (name, status) for name, status in field_status.items() 
            if status['is_protected']
        ]
        
        if not protected_fields:
            await callback.answer(_("No protected fields"))
            return
        
        message = f"🔒 **{_('Protected Data')}**\n\n"
        message += f"{_('These fields cannot be changed:')}\n\n"
        
        for field_name, status in protected_fields:
            value = format_field_value(status['current_value'], field_name, _)
            message += f"🔒 **{_(status['display_name'])}**: {value}\n"
        
        message += f"\n💡 {_('These fields are locked because they affect your credit score.')}"
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.back_to_personal_data(_),
            parse_mode="Markdown"
        )


@router.callback_query(F.data == "edit_available_fields")
async def show_editable_fields_menu(callback: types.CallbackQuery, _: callable):
    """Показать меню редактируемых полей"""
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer(_("User not found"))
            return
        
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if not personal_data:
            await callback.answer(_("Data not found"))
            return
        
        field_status = FieldProtectionManager.get_field_status(personal_data)
        
        message = f"✏️ **{_('Edit available fields')}**\n\n"
        message += f"{_('Select a field to edit:')}\n"
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.editable_fields_menu(field_status, _),
            parse_mode="Markdown"
        )


@router.callback_query(F.data.startswith("edit_field:"))
async def handle_field_edit_attempt(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Обработка попытки редактирования поля"""
    field_name = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer(_("User not found"))
            return
        
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if not personal_data:
            await callback.answer(_("Data not found"))
            return
        
        # Проверяем, защищено ли поле
        if FieldProtectionManager.is_field_protected(personal_data, field_name):
            # Показываем сообщение о защите
            reason = FieldProtectionManager.get_protection_reason(field_name, _)
            await callback.answer(
                f"🔒 {reason}",
                show_alert=True
            )
            return
        
        # Если поле не защищено, продолжаем редактирование
        await start_field_editing(callback, field_name, personal_data, state, _)


async def start_field_editing(callback: types.CallbackQuery, field_name: str, personal_data: PersonalData, state: FSMContext, _: callable):
    """Начать редактирование конкретного поля"""
    await state.update_data(
        editing_field=field_name,
        user_id=personal_data.user_id
    )
    
    # Определяем какое состояние установить и какое сообщение показать
    field_handlers = {
        'age': (PersonalDataStates.entering_age, _('Enter your age')),
        'work_experience_months': (PersonalDataStates.entering_work_experience, _('Enter work experience in months')),
        'address_stability_years': (PersonalDataStates.entering_address_stability, _('How many years have you lived at your current address?')),
        'closed_loans_count': (PersonalDataStates.entering_closed_loans, _('How many loans have you successfully closed?\n(enter 0 if none)')),
        'monthly_income': (PersonalDataStates.entering_income, _('Enter your monthly income')),
        'other_loans_monthly_payment': (PersonalDataStates.entering_other_loans_payment, _('Enter monthly payment for other loans'))
    }
    
    if field_name in field_handlers:
        state_to_set, message = field_handlers[field_name]
        await state.set_state(state_to_set)
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.cancel_button(_)
        )
    elif field_name == 'gender':
        await state.set_state(PersonalDataStates.choosing_gender)
        await callback.message.edit_text(
            _('Choose your gender'),
            reply_markup=Keyboards.gender_choice(_)
        )
    elif field_name == 'housing_status':
        await state.set_state(PersonalDataStates.choosing_housing_status)
        await callback.message.edit_text(
            _('Specify your housing status:'),
            reply_markup=Keyboards.housing_status_choice(_)
        )
    elif field_name == 'marital_status':
        await state.set_state(PersonalDataStates.choosing_marital_status)
        await callback.message.edit_text(
            _('Specify your marital status:'),
            reply_markup=Keyboards.marital_status_choice(_)
        )
    elif field_name == 'education':
        await state.set_state(PersonalDataStates.choosing_education)
        await callback.message.edit_text(
            _('Specify your education level:'),
            reply_markup=Keyboards.education_choice(_)
        )
    elif field_name == 'region':
        await state.set_state(PersonalDataStates.choosing_region)
        await callback.message.edit_text(
            _('In which region do you live?'),
            reply_markup=Keyboards.region_choice(_)
        )
    elif field_name == 'has_other_loans':
        await state.set_state(PersonalDataStates.choosing_has_loans)
        await callback.message.edit_text(
            _('Do you have other loans?'),
            reply_markup=Keyboards.yes_no_choice(_)
        )
    else:
        await callback.answer(_("This field cannot be edited"), show_alert=True)
        return
    
    await callback.answer()