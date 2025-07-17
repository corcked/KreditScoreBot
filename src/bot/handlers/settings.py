from aiogram import F, Router, types
from aiogram.filters import Command
from sqlalchemy import select, update

from src.bot.keyboards import Keyboards
from src.db.database import get_db_context
from src.db.models import User

router = Router(name="settings")


@router.callback_query(F.data == "settings")
async def show_settings(callback: types.CallbackQuery, _: callable):
    """Показать меню настроек"""
    await callback.message.edit_text(
        _("Settings"),
        reply_markup=Keyboards.settings_menu(_)
    )
    await callback.answer()


@router.callback_query(F.data == "change_language")
async def change_language(callback: types.CallbackQuery, _: callable):
    """Выбор языка"""
    async with get_db_context() as db:
        # Получаем текущий язык пользователя
        result = await db.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        current_lang = "ru"
        if user and user.language_code:
            current_lang = user.language_code
        
        # Формируем текст с текущим языком
        lang_name = _("Russian") if current_lang == "ru" else _("Uzbek")
        text = f"{_('Choose language')}\n\n{_('Current language')}: {lang_name}"
    
    await callback.message.edit_text(
        text,
        reply_markup=Keyboards.language_choice(_)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("lang:"))
async def process_language_choice(callback: types.CallbackQuery, _: callable):
    """Обработка выбора языка"""
    lang_code = callback.data.split(":")[1]
    
    async with get_db_context() as db:
        # Обновляем язык пользователя
        await db.execute(
            update(User)
            .where(User.telegram_id == callback.from_user.id)
            .values(language_code=lang_code)
        )
        await db.commit()
    
    # Отправляем сообщение на новом языке
    # Для этого нужно обновить контекст локализации
    from src.bot.utils.i18n import simple_gettext
    new_translate = lambda msg: simple_gettext(lang_code, msg)
    
    await callback.message.edit_text(
        f"✅ {new_translate('Language changed successfully')}",
        reply_markup=Keyboards.main_menu(new_translate)
    )
    await callback.answer()