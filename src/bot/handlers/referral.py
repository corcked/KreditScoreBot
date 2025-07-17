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
    help_text = """
📚 **Справка по использованию бота**

**Основные команды:**
/start - Начать работу с ботом
/menu - Главное меню
/my_app - Моя текущая заявка
/invite - Реферальная программа
/help - Эта справка

**Как пользоваться ботом:**

1️⃣ **Создание заявки**
   • Выберите тип кредита (автокредит или микрозайм)
   • Укажите сумму, ставку и срок
   • Введите ваш доход

2️⃣ **Расчет ПДН**
   • ПДН рассчитывается автоматически
   • 🟢 < 35% - отличный показатель
   • 🟡 35-50% - приемлемый показатель
   • 🔴 > 50% - высокая нагрузка

3️⃣ **Скоринг-балл**
   • Заполните персональные данные
   • Чем больше данных, тем выше балл
   • Приглашайте друзей для бонусов

4️⃣ **Отправка в банк**
   • Доступна при ПДН ≤ 50%
   • Заявка отправляется во все банки-партнеры
   • Ответ придет в течение 10 минут

**Есть вопросы?**
Обратитесь в поддержку: @kreditscore_support
"""
    
    await message.answer(
        help_text,
        parse_mode="Markdown",
        reply_markup=Keyboards.main_menu(_)
    )