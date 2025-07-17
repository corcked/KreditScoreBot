from decimal import Decimal

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import Keyboards
from src.bot.states import LoanApplicationStates
from src.bot.utils import (
    format_amount,
    format_loan_summary,
    validate_amount,
    validate_positive_number,
    validate_rate,
    validate_term,
)
from src.core.enums import CarCondition, LoanStatus, LoanType, ReceiveMethod
from src.core.pdn import PDNCalculator
from src.db.database import get_db_context
from src.db.models import LoanApplication, PersonalData, User

router = Router(name="loan")


@router.callback_query(F.data == "new_loan")
async def start_new_loan(callback: types.CallbackQuery, state: FSMContext):
    """Начало создания новой заявки"""
    await callback.message.edit_text(
        "Выберите тип кредита:\n\n"
        "🚗 **Автокредит**\n"
        "• До 1 млрд сум\n"
        "• Ставка: 4-48%\n"
        "• Срок: 6 мес - 5 лет\n\n"
        "💰 **Микрозайм**\n"
        "• До 100 млн сум\n"
        "• Ставка: 18-79%\n"
        "• Срок: 1 мес - 3 года",
        reply_markup=Keyboards.loan_type_choice(),
        parse_mode="Markdown"
    )
    await state.set_state(LoanApplicationStates.choosing_loan_type)
    await callback.answer()


@router.callback_query(LoanApplicationStates.choosing_loan_type, F.data.startswith("loan_type:"))
async def process_loan_type(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора типа кредита"""
    loan_type = callback.data.split(":")[1]
    await state.update_data(loan_type=loan_type)
    
    if loan_type == LoanType.CARLOAN.value:
        await callback.message.edit_text(
            "Выберите состояние автомобиля:",
            reply_markup=Keyboards.car_condition_choice()
        )
        await state.set_state(LoanApplicationStates.choosing_car_condition)
    else:
        await callback.message.edit_text(
            "Выберите способ получения денег:",
            reply_markup=Keyboards.receive_method_choice()
        )
        await state.set_state(LoanApplicationStates.choosing_receive_method)
    
    await callback.answer()


@router.callback_query(LoanApplicationStates.choosing_car_condition, F.data.startswith("car:"))
async def process_car_condition(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора состояния автомобиля"""
    car_condition = callback.data.split(":")[1]
    await state.update_data(car_condition=car_condition)
    
    limits = PDNCalculator.LOAN_LIMITS[LoanType.CARLOAN]
    
    await callback.message.edit_text(
        f"Введите сумму кредита (до {format_amount(limits['max_amount'])} сум):",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(LoanApplicationStates.entering_amount)
    await callback.answer()


@router.callback_query(LoanApplicationStates.choosing_receive_method, F.data.startswith("receive:"))
async def process_receive_method(callback: types.CallbackQuery, state: FSMContext):
    """Обработка выбора способа получения"""
    receive_method = callback.data.split(":")[1]
    await state.update_data(receive_method=receive_method)
    
    limits = PDNCalculator.LOAN_LIMITS[LoanType.MICROLOAN]
    
    await callback.message.edit_text(
        f"Введите сумму кредита (до {format_amount(limits['max_amount'])} сум):",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(LoanApplicationStates.entering_amount)
    await callback.answer()


@router.message(LoanApplicationStates.entering_amount)
async def process_amount(message: types.Message, state: FSMContext):
    """Обработка введенной суммы"""
    data = await state.get_data()
    loan_type = LoanType(data["loan_type"])
    limits = PDNCalculator.LOAN_LIMITS[loan_type]
    
    valid, amount, error = validate_amount(message.text, limits["max_amount"])
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(amount=amount)
    
    await message.answer(
        f"Введите процентную ставку ({limits['min_rate']}-{limits['max_rate']}%):",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(LoanApplicationStates.entering_rate)


@router.message(LoanApplicationStates.entering_rate)
async def process_rate(message: types.Message, state: FSMContext):
    """Обработка введенной ставки"""
    data = await state.get_data()
    loan_type = LoanType(data["loan_type"])
    limits = PDNCalculator.LOAN_LIMITS[loan_type]
    
    valid, rate, error = validate_rate(
        message.text,
        Decimal(limits["min_rate"]),
        Decimal(limits["max_rate"])
    )
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(rate=rate)
    
    min_term = limits["min_term_months"]
    max_term = limits["max_term_months"]
    
    await message.answer(
        f"Введите срок кредита в месяцах ({min_term}-{max_term}):",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(LoanApplicationStates.entering_term)


@router.message(LoanApplicationStates.entering_term)
async def process_term(message: types.Message, state: FSMContext):
    """Обработка введенного срока"""
    data = await state.get_data()
    loan_type = LoanType(data["loan_type"])
    limits = PDNCalculator.LOAN_LIMITS[loan_type]
    
    valid, term, error = validate_term(
        message.text,
        limits["min_term_months"],
        limits["max_term_months"]
    )
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(term_months=term)
    
    await message.answer(
        "Введите ваш ежемесячный доход (сум):",
        reply_markup=Keyboards.cancel_button()
    )
    await state.set_state(LoanApplicationStates.entering_income)


@router.message(LoanApplicationStates.entering_income)
async def process_income(message: types.Message, state: FSMContext):
    """Обработка введенного дохода"""
    valid, income, error = validate_amount(message.text, 10**12)  # Максимум триллион
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.cancel_button())
        return
    
    await state.update_data(income=income)
    
    await message.answer(
        "Есть ли у вас ежемесячные платежи по другим кредитам?\n"
        "Если да, введите общую сумму. Если нет, нажмите 'Пропустить'.",
        reply_markup=Keyboards.skip_other_payments()
    )
    await state.set_state(LoanApplicationStates.entering_other_payments)


@router.callback_query(LoanApplicationStates.entering_other_payments, F.data == "skip_other_payments")
async def skip_other_payments(callback: types.CallbackQuery, state: FSMContext):
    """Пропуск ввода других платежей"""
    await state.update_data(other_payments=Decimal("0"))
    await show_loan_confirmation(callback.message, state)
    await callback.answer()


@router.message(LoanApplicationStates.entering_other_payments)
async def process_other_payments(message: types.Message, state: FSMContext):
    """Обработка других платежей"""
    valid, payments, error = validate_amount(message.text, 10**12)
    
    if not valid:
        await message.answer(f"❌ {error}", reply_markup=Keyboards.skip_other_payments())
        return
    
    await state.update_data(other_payments=payments)
    await show_loan_confirmation(message, state)


async def show_loan_confirmation(message: types.Message, state: FSMContext):
    """Показ подтверждения заявки"""
    data = await state.get_data()
    
    # Расчет аннуитетного платежа
    monthly_payment = PDNCalculator.calculate_annuity_payment(
        data["amount"],
        data["rate"],
        data["term_months"]
    )
    
    # Расчет ПДН
    pdn_value = PDNCalculator.calculate_pdn(
        monthly_payment,
        data["income"],
        data.get("other_payments", Decimal("0"))
    )
    
    # Сохраняем расчетные данные
    await state.update_data(
        monthly_payment=monthly_payment,
        pdn_value=pdn_value
    )
    
    # Получаем статус ПДН
    pdn_status = PDNCalculator.get_pdn_status(pdn_value)
    pdn_emoji = PDNCalculator.get_pdn_emoji(pdn_status)
    
    # Форматируем сводку
    summary = format_loan_summary(data)
    summary += f"\n{pdn_emoji} **ПДН: {pdn_value}%**\n"
    
    if not PDNCalculator.can_get_loan(pdn_value):
        summary += "\n⚠️ **Внимание!** При ПДН > 50% банки не смогут выдать кредит."
    
    await message.answer(
        f"Проверьте данные заявки:\n\n{summary}\n\nВсе верно?",
        reply_markup=Keyboards.confirm_application(),
        parse_mode="Markdown"
    )
    await state.set_state(LoanApplicationStates.confirming_application)


@router.callback_query(LoanApplicationStates.confirming_application, F.data == "confirm_app")
async def confirm_application(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение и сохранение заявки"""
    data = await state.get_data()
    
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return
        
        # Архивируем старые заявки
        await db.execute(
            update(LoanApplication)
            .where(LoanApplication.user_id == user.id)
            .where(LoanApplication.is_archived == False)
            .values(is_archived=True)
        )
        
        # Создаем новую заявку
        application = LoanApplication(
            user_id=user.id,
            loan_type=LoanType(data["loan_type"]),
            amount=data["amount"],
            annual_rate=data["rate"],
            term_months=data["term_months"],
            car_condition=CarCondition(data["car_condition"]) if data.get("car_condition") else None,
            receive_method=ReceiveMethod(data["receive_method"]) if data.get("receive_method") else None,
            monthly_payment=data["monthly_payment"],
            pdn_value=data["pdn_value"],
            status=LoanStatus.NEW
        )
        
        db.add(application)
        
        # Обновляем доход в персональных данных
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        if personal_data:
            personal_data.monthly_income = data["income"]
            if data.get("other_payments"):
                personal_data.has_other_loans = True
                personal_data.other_loans_monthly_payment = data["other_payments"]
        
        await db.commit()
    
    # Получаем описание ПДН
    pdn_status = PDNCalculator.get_pdn_status(data["pdn_value"])
    pdn_description = PDNCalculator.get_pdn_description(data["pdn_value"], pdn_status)
    
    can_send = PDNCalculator.can_get_loan(data["pdn_value"])
    
    await callback.message.edit_text(
        f"✅ Заявка успешно создана!\n\n"
        f"{pdn_description}\n\n"
        f"Что дальше?",
        reply_markup=Keyboards.application_actions(can_send=can_send),
        parse_mode="Markdown"
    )
    
    await state.clear()
    await callback.answer("Заявка создана!")


@router.callback_query(LoanApplicationStates.confirming_application, F.data == "cancel_app")
async def cancel_application(callback: types.CallbackQuery, state: FSMContext):
    """Отмена создания заявки"""
    await callback.message.edit_text(
        "Создание заявки отменено.",
        reply_markup=Keyboards.main_menu()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cancel_any(callback: types.CallbackQuery, state: FSMContext):
    """Универсальная отмена"""
    await callback.message.edit_text(
        "Действие отменено.",
        reply_markup=Keyboards.main_menu()
    )
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "my_applications")
async def show_applications(callback: types.CallbackQuery):
    """Показ заявок пользователя"""
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer("Ошибка: пользователь не найден", show_alert=True)
            return
        
        # Получаем активную заявку
        result = await db.execute(
            select(LoanApplication)
            .where(LoanApplication.user_id == user.id)
            .where(LoanApplication.is_archived == False)
            .order_by(LoanApplication.created_at.desc())
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.message.edit_text(
                "У вас нет активных заявок.\n\n"
                "Создайте новую заявку для расчета долговой нагрузки.",
                reply_markup=Keyboards.main_menu()
            )
            await callback.answer()
            return
        
        # Форматируем информацию о заявке
        loan_type = "Автокредит" if application.loan_type == LoanType.CARLOAN else "Микрозайм"
        
        status_text = {
            LoanStatus.NEW: "🆕 Новая",
            LoanStatus.SENT: "📤 Отправлена в банк",
            LoanStatus.ARCHIVED: "📁 В архиве"
        }[application.status]
        
        pdn_status = PDNCalculator.get_pdn_status(application.pdn_value)
        pdn_emoji = PDNCalculator.get_pdn_emoji(pdn_status)
        
        text = f"**Ваша текущая заявка**\n\n"
        text += f"📅 Дата: {application.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"📊 Статус: {status_text}\n\n"
        text += f"**{loan_type}**\n"
        text += f"💰 Сумма: {format_amount(application.amount)} сум\n"
        text += f"📊 Ставка: {application.annual_rate}%\n"
        text += f"📅 Срок: {application.term_months} мес.\n"
        text += f"💳 Платеж: {format_amount(application.monthly_payment)} сум\n"
        text += f"{pdn_emoji} ПДН: {application.pdn_value}%\n"
        
        can_send = (
            application.status == LoanStatus.NEW and
            PDNCalculator.can_get_loan(application.pdn_value)
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=Keyboards.application_actions(can_send=can_send),
            parse_mode="Markdown"
        )
    
    await callback.answer()