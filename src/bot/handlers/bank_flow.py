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
async def start_send_to_bank(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Начало процесса отправки в банк"""
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.answer(_('Error: user not found'), show_alert=True)
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
            await callback.answer(_('Active application not found'), show_alert=True)
            return
        
        # Проверяем ПДН
        if application.pdn_value > 50:
            await callback.answer(
                _("With DTI > 50% banks won't approve loan"),
                show_alert=True
            )
            return
        
        await state.update_data(application_id=application.id)
        
        confirm_text = (
            f"🏦 **{_('Send application to banks')}**\n\n"
            f"{_('Your application will be sent to all partner banks.')}\n"
            f"{_('Banks will review application and send offers.')}\n\n"
            f"⏱ {_('Estimated wait time: 10 minutes')}\n\n"
            f"{_('Send application?')}"
        )
        
        keyboard = [
            [
                types.InlineKeyboardButton(text=f"✅ {_('Send')}", callback_data="confirm_send"),
                types.InlineKeyboardButton(text=f"❌ {_('Cancel')}", callback_data="cancel_send"),
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
async def confirm_send_to_bank(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Подтверждение отправки в банк"""
    data = await state.get_data()
    application_id = data.get("application_id")
    
    if not application_id:
        await callback.answer(_('Error: application not found'), show_alert=True)
        return
    
    async with get_db_context() as db:
        # Обновляем статус заявки
        result = await db.execute(
            select(LoanApplication).where(LoanApplication.id == application_id)
        )
        application = result.scalar_one_or_none()
        
        if not application:
            await callback.answer(_('Error: application not found'), show_alert=True)
            return
        
        application.status = LoanStatus.SENT
        application.sent_to_bank_at = datetime.utcnow()
        await db.commit()
    
    # Отправляем уведомление
    await callback.message.edit_text(
        f"✅ **{_('Application sent successfully!')}**\n\n"
        f"{_('Your application sent to all partner banks.')}\n"
        f"{_('We will notify you when we receive responses.')}\n\n"
        f"📱 {_('Wait for SMS with offers from banks.')}",
        reply_markup=Keyboards.main_menu(_),
        parse_mode="Markdown"
    )
    
    await state.clear()
    await callback.answer(_('Application sent!'))
    
    # Запускаем симуляцию ответа банка
    asyncio.create_task(simulate_bank_response(callback.bot, callback.from_user.id, application_id))


@router.callback_query(BankFlowStates.confirming_send, F.data == "cancel_send")
async def cancel_send_to_bank(callback: types.CallbackQuery, state: FSMContext, _: callable):
    """Отмена отправки в банк"""
    await callback.message.edit_text(
        _('Send canceled.'),
        reply_markup=Keyboards.main_menu(_)
    )
    await state.clear()
    await callback.answer()


async def simulate_bank_response(bot, user_telegram_id: int, application_id: int):
    """Симуляция ответа от банка"""
    # Ждем указанное время
    await asyncio.sleep(settings.bank_response_delay_minutes * 60)
    
    async with get_db_context() as db:
        # Получаем язык пользователя
        from src.bot.i18n import simple_gettext
        result = await db.execute(
            select(User).where(User.telegram_id == user_telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return
        
        lang_code = user.language_code or 'ru'
        _ = lambda msg: simple_gettext(lang_code, msg)
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
                (_("Kapitalbank"), application.annual_rate - 2),
                (_("Uzpromstroybank"), application.annual_rate - 1),
                (_("Ipoteka-bank"), application.annual_rate),
                (_("Hamkorbank"), application.annual_rate + 1),
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
                response_text = f"📱 **{_('SMS from banks received!')}**\n\n"
                response_text += f"{_('Offers received:')}\n\n"
                
                for bank_name, rate in valid_banks[:3]:  # Показываем до 3 банков
                    response_text += f"🏦 **{bank_name}**\n"
                    response_text += f"   {_('Rate')}: {rate}%\n"
                    response_text += f"   {_('Status: Pre-approved')}\n\n"
                
                response_text += _('Contact selected bank to complete loan.')
                
                bank_response = _('Approved by {count} banks').format(count=len(valid_banks))
            else:
                response_text = (
                    f"📱 **{_('Response from banks received')}**\n\n"
                    f"{_('Unfortunately, your application was not approved.')}\n"
                    f"{_('Recommend improving credit history and try later.')}"
                )
                bank_response = _('Declined')
        else:
            response_text = (
                f"📱 **{_('Response from banks received')}**\n\n"
                f"{_('Unfortunately, your application was not approved.')}\n"
                f"{_('Possible reasons:')}\n"
                f"• {_('Insufficient income')}\n"
                f"• {_('No credit history')}\n"
                f"• {_('High debt burden')}\n\n"
                f"{_('Try applying in 3 months.')}"
            )
            bank_response = _('Declined')
        
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
async def show_my_application_command(message: types.Message, _: callable):
    """Команда для показа текущей заявки"""
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                _('You are not registered. Use /start to begin.')
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
                f"{_('You have no active applications.')}\n\n"
                f"{_('Create new application for debt burden calculation.')}",
                reply_markup=Keyboards.main_menu(_)
            )
            return
        
        # Форматируем информацию о заявке
        from src.bot.utils import format_amount
        from src.core.pdn import PDNCalculator
        
        loan_type = _('Car loan') if application.loan_type.value == "carloan" else _('Microloan')
        
        status_text = {
            LoanStatus.NEW: f"🆕 {_('New')}",
            LoanStatus.SENT: f"📤 {_('Sent to bank')}",
            LoanStatus.ARCHIVED: f"📁 {_('Archived')}"
        }[application.status]
        
        pdn_status = PDNCalculator.get_pdn_status(application.pdn_value)
        pdn_emoji = PDNCalculator.get_pdn_emoji(pdn_status)
        
        text = f"**{_('Your current application')}**\n\n"
        text += f"📅 {_('Date')}: {application.created_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"📊 {_('Status')}: {status_text}\n"
        
        if application.status == LoanStatus.SENT and application.bank_response:
            text += f"🏦 {_('Banks response')}: {application.bank_response}\n"
        
        text += f"\n**{loan_type}**\n"
        text += f"💰 {_('Amount')}: {format_amount(application.amount)} {_('sum')}\n"
        text += f"📊 {_('Rate')}: {application.annual_rate}%\n"
        text += f"📅 {_('Term')}: {application.term_months} {_('months')}\n"
        text += f"💳 {_('Monthly payment')}: {format_amount(application.monthly_payment)} {_('sum')}\n"
        text += f"{pdn_emoji} {_('DTI')}: {application.pdn_value}%"
        
        can_send = (
            application.status == LoanStatus.NEW and
            PDNCalculator.can_get_loan(application.pdn_value)
        )
        
        await message.answer(
            text,
            reply_markup=Keyboards.application_actions(_, can_send=can_send),
            parse_mode="Markdown"
        )