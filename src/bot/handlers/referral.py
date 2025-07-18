from aiogram import F, Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.bot.keyboards import Keyboards
from src.config.settings import settings
from src.core.referral import ReferralSystem
from src.db.database import get_db_context
from src.db.models import User

router = Router(name="referral")


@router.callback_query(F.data == "referral")
@router.message(Command("invite"))
async def show_referral_program(event: types.Message | types.CallbackQuery, state: FSMContext, _: callable):
    """Показать реферальную программу"""
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
        
        # Генерируем реферальную ссылку
        referral_link = ReferralSystem.generate_referral_link(
            settings.bot_username,
            user.telegram_id
        )
        
        # Получаем количество рефералов
        referral_count = user.referral_count
        
        # Форматируем сообщение
        text = ReferralSystem.format_referral_message(referral_link, referral_count, _)
        
        # Создаем URL для шаринга
        share_url = ReferralSystem.create_share_button_url(referral_link, _)
        
        # Отправляем сообщение
        if is_callback:
            await message.edit_text(
                text,
                reply_markup=Keyboards.referral_menu(_, share_url),
                parse_mode="Markdown"
            )
            await event.answer()
        else:
            await message.answer(
                text,
                reply_markup=Keyboards.referral_menu(_, share_url),
                parse_mode="Markdown"
            )
    
    await state.clear()




@router.message(Command("help"))
async def show_help(message: types.Message, _: callable):
    """Показать справку"""
    help_text = f"""
📚 **{_('Bot Usage Guide')}**

**{_('Main commands')}:**
/start - {_('Start using the bot')}
/menu - {_('Main menu')}
/my_app - {_('My current application')}
/invite - {_('Referral program')}
/help - {_('This help')}

**{_('How to use the bot')}:**

1️⃣ **{_('Creating an application')}**
   • {_('Choose loan type (car loan or microloan)')}
   • {_('Specify amount, rate and term')}
   • {_('Enter your income')}

2️⃣ **{_('DTI calculation')}**
   • {_('DTI is calculated automatically')}
   • 🟢 < 35% - {_('excellent indicator')}
   • 🟡 35-50% - {_('acceptable indicator')}
   • 🔴 > 50% - {_('high load')}

3️⃣ **{_('Credit score')}**
   • {_('Fill in personal data')}
   • {_('The more data, the higher the score')}
   • {_('Invite friends for bonuses')}

4️⃣ **{_('Sending to bank')}**
   • {_('Available when DTI ≤ 50%')}
   • {_('Application is sent to all partner banks')}
   • {_('Response will come within 10 minutes')}

**{_('Have questions?')}**
{_('Contact support')}: @kreditscore_support
"""
    
    await message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=Keyboards.main_menu(_)
    )