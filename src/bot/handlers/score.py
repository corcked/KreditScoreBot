from aiogram import F, Router, types
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import Keyboards
from src.bot.utils import format_amount
from src.core.enums import LoanStatus
from src.core.pdn import PDNCalculator
from src.core.scoring import PersonalData as PersonalDataSchema, ScoringCalculator
from src.db.database import get_db_context
from src.db.models import LoanApplication, PersonalData, User

router = Router(name="score")


@router.message(Command("score"))
@router.callback_query(F.data == "my_score")
async def show_score(event: types.Message | types.CallbackQuery, _: callable):
    """Показать текущие показатели ПДН и скоринга"""
    # Определяем тип события
    if isinstance(event, types.CallbackQuery):
        message = event.message
        user_id = event.from_user.id
        is_callback = True
    else:
        message = event
        user_id = event.from_user.id
        is_callback = False
    
    async with get_db_context() as db:
        # Получаем пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            error_text = _('You are not registered. Use /start to begin.')
            if is_callback:
                await event.answer(error_text, show_alert=True)
            else:
                await message.answer(error_text)
            return
        
        # Получаем активную заявку для ПДН
        result = await db.execute(
            select(LoanApplication)
            .where(LoanApplication.user_id == user.id)
            .where(LoanApplication.is_archived == False)
            .order_by(LoanApplication.created_at.desc())
        )
        application = result.scalar_one_or_none()
        
        # Получаем персональные данные для скоринга
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user.id)
        )
        personal_data = result.scalar_one_or_none()
        
        # Формируем сообщение
        text = f"📊 **{_('Your financial indicators')}**\n\n"
        
        # Раздел ПДН
        text += f"💳 **{_('Debt burden indicator (DTI)')}**\n"
        if application:
            pdn_status = PDNCalculator.get_pdn_status(application.pdn_value)
            pdn_emoji = PDNCalculator.get_pdn_emoji(pdn_status)
            
            text += f"{pdn_emoji} {_('DTI')}: **{application.pdn_value}%**\n"
            
            # Описание статуса
            if pdn_status.value == "green":
                text += f"✅ {_('Excellent indicator!')}\n"
            elif pdn_status.value == "yellow":
                text += f"⚠️ {_('Acceptable indicator')}\n"
            else:
                text += f"❌ {_('High debt burden')}\n"
            
            # Детали расчета
            text += f"\n{_('Calculation details')}:\n"
            text += f"• {_('Monthly payment')}: {format_amount(application.monthly_payment)} {_('sum')}\n"
            
            if personal_data and personal_data.monthly_income:
                text += f"• {_('Income')}: {format_amount(personal_data.monthly_income)} {_('sum')}\n"
                
                if personal_data.has_other_loans and personal_data.other_loans_monthly_payment:
                    text += f"• {_('Other payments')}: {format_amount(personal_data.other_loans_monthly_payment)} {_('sum')}\n"
            
            # Возможность получения кредита
            if PDNCalculator.can_get_loan(application.pdn_value):
                text += f"\n✅ {_('Banks may approve the loan')}\n"
            else:
                text += f"\n❌ {_('Banks do not issue loans with DTI > 50%')}\n"
        else:
            text += f"📋 {_('You have no active applications')}\n"
            text += f"{_('Create application to calculate DTI')}\n"
        
        # Раздел Скоринга
        text += f"\n🎯 **{_('Credit scoring')}**\n"
        if personal_data and personal_data.current_score > 0:
            score = personal_data.current_score
            level = ScoringCalculator.get_score_level(score)
            
            text += f"{_('Your score')}: **{score}** ({level})\n"
            
            # Шкала прогресса
            min_score = 300
            max_score = 900
            score_range = max_score - min_score
            score_position = score - min_score
            progress = int((score_position / score_range) * 10)
            
            progress_bar = "["
            for i in range(10):
                if i < progress:
                    progress_bar += "▰"
                else:
                    progress_bar += "▱"
            progress_bar += "]"
            
            text += f"{progress_bar}\n"
            text += f"300 {'─' * 20} 900\n"
            
            # Процент заполненности профиля
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
            
            text += f"\n📝 {_('Profile completion')} {completion}%\n"
            
            if completion < 100:
                text += f"💡 {_('Fill in all data to increase score')}\n"
        else:
            text += f"❓ {_('Scoring not calculated')}\n"
            text += f"{_('Fill personal data for calculation')}\n"
        
        # Кнопки действий
        keyboard = []
        
        if not application:
            keyboard.append([types.InlineKeyboardButton(
                text=f"💳 {_('Create application')}",
                callback_data="new_loan"
            )])
        
        if not personal_data or personal_data.current_score == 0:
            keyboard.append([types.InlineKeyboardButton(
                text=f"👤 {_('Fill data')}",
                callback_data="personal_data"
            )])
        elif completion < 100:
            keyboard.append([types.InlineKeyboardButton(
                text=f"📝 {_('Complete data')}",
                callback_data="personal_data"
            )])
        
        keyboard.append([types.InlineKeyboardButton(
            text=f"🔙 {_('Main menu')}",
            callback_data="main_menu"
        )])
        
        reply_markup = types.InlineKeyboardMarkup(inline_keyboard=keyboard)
        
        # Отправляем ответ
        if is_callback:
            await message.edit_text(
                text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )
            await event.answer()
        else:
            await message.answer(
                text,
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )