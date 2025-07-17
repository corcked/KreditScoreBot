import asyncio
import random
from datetime import datetime, timedelta

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import Keyboards
from src.bot.states import BankFlowStates
from src.config.settings import settings
from src.core.enums import LoanStatus
from src.db.database import get_db_context
from src.db.models import LoanApplication, User

router = Router(name="bank_flow")


@router.callback_query(F.data == "send_to_bank")
async def start_send_to_bank(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса отправки в банк"""
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
            .where(LoanApplication.status == LoanStatus.NEW)
            .order_by(LoanApplication.created_at.desc())
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer("Активная заявка не найдена", show_alert=True)
            return
        
        # Проверяем ПДН
        if application.pdn_value > 50:
            await callback.answer(
                "При ПДН > 50% банки не смогут выдать кредит",
                show_alert=True
            )
            return
        
        await state.update_data(application_id=application.id)
        
        confirm_text = (
            "🏦 **Отправка заявки в банки**\n\n"
            "Ваша заявка будет отправлена во все банки-партнеры.\n"
            "Банки рассмотрят заявку и отправят предложения.\n\n"
            "⏱ Примерное время ожидания: 10 минут\n\n"
            "Отправить заявку?"
        )
        
        keyboard = [
            [
                types.InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_send"),
                types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send"),
            ]
        ]
        
        await callback.message.edit_text(
            confirm_text,
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=keyboard),
            parse_mode="Markdown"
        )
        
        await state.set_state(BankFlowStates.confirming_send)
    
    await callback.answer()


@router.callback_query(BankFlowStates.confirming_send, F.data == "confirm_send")
async def confirm_send_to_bank(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение отправки в банк"""
    data = await state.get_data()
    application_id = data.get("application_id")
    
    if not application_id:
        await callback.answer("Ошибка: заявка не найдена", show_alert=True)
        return
    
    async with get_db_context() as db:
        # Обновляем статус заявки
        result = await db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer("Ошибка: заявка не найдена", show_alert=True)
            return
        
        application.status = LoanStatus.SENT
        application.sent_to_bank_at = datetime.utcnow()
        await db.commit()
    
    # Отправляем уведомление
    await callback.message.edit_text(
        "✅ **Заявка успешно отправлена!**\n\n"
        "Ваша заявка отправлена во все банки-партнеры.\n"
        "Мы уведомим вас, как только получим ответы.\n\n"
        "📱 Ожидайте SMS с предложениями от банков.",
        reply_markup=Keyboards.main_menu(),
        parse_mode="Markdown"
    )
    
    await state.clear()
    await callback.answer("Заявка отправлена!")
    
    # Запускаем симуляцию ответа банка
    asyncio.create_task(simulate_bank_response(callback.bot, callback.from_user.id, application_id))


@router.callback_query(BankFlowStates.confirming_send, F.data == "cancel_send")
async def cancel_send_to_bank(callback: types.CallbackQuery, state: FSMContext):
    """Отмена отправки в банк"""
    await callback.message.edit_text(
        "Отправка заявки отменена.",
        reply_markup=Keyboards.main_menu()
    )
    await state.clear()
    await callback.answer()


async def simulate_bank_response(bot, user_telegram_id: int, application_id: int):
    """Симуляция ответа от банка"""
    # Ждем указанное время
    await asyncio.sleep(settings.bank_response_delay_minutes * 60)
    
    async with get_db_context() as db:
        # Получаем заявку
        result = await db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application or application.status != LoanStatus.SENT:
            return
        
        # Симулируем ответ банка
        is_approved = random.random() < settings.bank_approval_probability
        
        if is_approved:
            # Генерируем "предложения" от банков
            banks = [
                ("Капиталбанк", application.annual_rate - 2),
                ("Узпромстройбанк", application.annual_rate - 1),
                ("Ипотека-банк", application.annual_rate),
                ("Хамкорбанк", application.annual_rate + 1),
            ]
            
            # Фильтруем банки с валидными ставками
            valid_banks = []
            for bank_name, rate in banks:
                if application.loan_type.value == "carloan":
                    if 4 <= rate <= 48:
                        valid_banks.append((bank_name, rate))
                else:  # microloan
                    if 18 <= rate <= 79:
                        valid_banks.append((bank_name, rate))
            
            if valid_banks:
                response_text = "📱 **SMS от банков получена!**\n\n"
                response_text += "Поступили предложения:\n\n"
                
                for bank_name, rate in valid_banks[:3]:  # Показываем до 3 банков
                    response_text += f"🏦 **{bank_name}**\n"
                    response_text += f"   Ставка: {rate}%\n"
                    response_text += f"   Статус: ✅ Предварительно одобрено\n\n"
                
                response_text += "Для оформления кредита обратитесь в выбранный банк."
                
                bank_response = f"Одобрено {len(valid_banks)} банками"
            else:
                response_text = (
                    "📱 **Ответ от банков получен**\n\n"
                    "К сожалению, ваша заявка не была одобрена.\n"
                    "Рекомендуем улучшить кредитную историю и попробовать позже."
                )
                bank_response = "Отклонено"
        else:
            response_text = (
                "📱 **Ответ от банков получен**\n\n"
                "К сожалению, ваша заявка не была одобрена.\n"
                "Возможные причины:\n"
                "• Недостаточный доход\n"
                "• Отсутствие кредитной истории\n"
                "• Высокая долговая нагрузка\n\n"
                "Попробуйте подать заявку через 3 месяца."
            )
            bank_response = "Отклонено"
        
        # Обновляем заявку
        application.bank_response_at = datetime.utcnow()
        application.bank_response = bank_response
        await db.commit()
        
        # Отправляем уведомление пользователю
        try:
            await bot.send_message(
                user_telegram_id,
                response_text,
                parse_mode="Markdown"
            )
        except Exception:
            # Игнорируем ошибки отправки
            pass


@router.message(F.text == "/my_app")
async def show_my_application_command(message: types.Message):
    """Команда для показа текущей заявки"""
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                "Вы еще не зарегистрированы. Используйте /start для начала."
            )
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
            await message.answer(
                "У вас нет активных заявок.\n\n"
                "Создайте новую заявку для расчета долговой нагрузки.",
                reply_markup=Keyboards.main_menu()
            )
            return
        
        # Форматируем информацию о заявке
        from src.bot.utils import format_amount
        from src.core.pdn import PDNCalculator
        
        loan_type = "Автокредит" if application.loan_type.value == "carloan" else "Микрозайм"
        
        status_text = {
            LoanStatus.NEW: "🆕 Новая",
            LoanStatus.SENT: "📤 Отправлена в банк",
            LoanStatus.ARCHIVED: "📁 В архиве"
        }[application.status]
        
        pdn_status = PDNCalculator.get_pdn_status(application.pdn_value)
        pdn_emoji = PDNCalculator.get_pdn_emoji(pdn_status)
        
        text = f"**Ваша текущая заявка**\n\n"
        text += f"📅 Дата: {application.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"📊 Статус: {status_text}\n"
        
        if application.status == LoanStatus.SENT and application.bank_response:
            text += f"🏦 Ответ банков: {application.bank_response}\n"
        
        text += f"\n**{loan_type}**\n"
        text += f"💰 Сумма: {format_amount(application.amount)} сум\n"
        text += f"📊 Ставка: {application.annual_rate}%\n"
        text += f"📅 Срок: {application.term_months} мес.\n"
        text += f"💳 Платеж: {format_amount(application.monthly_payment)} сум\n"
        text += f"{pdn_emoji} ПДН: {application.pdn_value}%"
        
        can_send = (
            application.status == LoanStatus.NEW and
            PDNCalculator.can_get_loan(application.pdn_value)
        )
        
        await message.answer(
            text,
            reply_markup=Keyboards.application_actions(can_send=can_send),
            parse_mode="Markdown"
        )