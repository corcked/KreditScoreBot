import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram import types
from aiogram.fsm.context import FSMContext

from src.bot.handlers.personal_data import (
    show_personal_data_menu,
    explain_field_protection,
    view_protected_data,
    handle_field_edit_attempt,
    show_editable_fields_menu
)
from src.core.field_protection import FieldProtectionManager
from src.db.models import PersonalData, User
from src.core.enums import Gender, HousingStatus, Education


@pytest.fixture
def mock_callback():
    """Создает mock callback query"""
    callback = AsyncMock(spec=types.CallbackQuery)
    callback.from_user = MagicMock()
    callback.from_user.id = 12345
    callback.message = AsyncMock()
    callback.message.edit_text = AsyncMock()
    callback.answer = AsyncMock()
    callback.data = ""
    return callback


@pytest.fixture
def mock_state():
    """Создает mock FSM state"""
    state = AsyncMock(spec=FSMContext)
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()
    state.get_data = AsyncMock(return_value={})
    return state


@pytest.fixture
def mock_db():
    """Создает mock database session"""
    db = AsyncMock()
    db.execute = AsyncMock()
    db.commit = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Создает mock user"""
    user = User()
    user.id = 1
    user.telegram_id = 12345
    user.referral_count = 0
    return user


class TestPersonalDataProtectionUI:
    """Тесты UI защиты персональных данных"""
    
    @pytest.mark.asyncio
    async def test_show_menu_with_empty_data(self, mock_callback, mock_db, mock_user):
        """Тест отображения меню с пустыми данными"""
        personal_data = PersonalData(user_id=mock_user.id)
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await show_personal_data_menu(mock_callback, lambda x: x)
            
            # Проверяем, что сообщение содержит информацию о доступных полях
            call_args = mock_callback.message.edit_text.call_args
            message_text = call_args[0][0]
            
            assert "Personal Data" in message_text
            assert "Available for editing" in message_text
            assert "Protected fields" not in message_text
    
    @pytest.mark.asyncio
    async def test_show_menu_with_protected_data(self, mock_callback, mock_db, mock_user):
        """Тест отображения меню с защищенными данными"""
        personal_data = PersonalData(
            user_id=mock_user.id,
            age=30,
            gender=Gender.FEMALE,
            monthly_income=100000,
            current_score=650
        )
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await show_personal_data_menu(mock_callback, lambda x: x)
            
            call_args = mock_callback.message.edit_text.call_args
            message_text = call_args[0][0]
            
            assert "Protected fields" in message_text
            assert "🔒" in message_text
            assert "30" in message_text  # Возраст
            assert "Female" in message_text  # Пол
            assert "100 000" in message_text  # Доход (форматированный)
            assert "650" in message_text  # Скоринг
    
    @pytest.mark.asyncio
    async def test_field_edit_attempt_protected(self, mock_callback, mock_db, mock_state, mock_user):
        """Тест попытки редактирования защищенного поля"""
        personal_data = PersonalData(user_id=mock_user.id, age=30)
        mock_callback.data = "edit_field:age"
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await handle_field_edit_attempt(mock_callback, mock_state, lambda x: x)
            
            # Проверяем, что показано предупреждение
            mock_callback.answer.assert_called_once()
            call_args = mock_callback.answer.call_args
            assert "🔒" in call_args[0][0]
            assert call_args[1]['show_alert'] is True
            
            # Проверяем, что редактирование не началось
            mock_state.set_state.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_field_edit_attempt_editable(self, mock_callback, mock_db, mock_state, mock_user):
        """Тест попытки редактирования доступного поля"""
        personal_data = PersonalData(user_id=mock_user.id, monthly_income=100000)
        mock_callback.data = "edit_field:monthly_income"
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            with patch('src.bot.handlers.personal_data.start_field_editing') as mock_start:
                await handle_field_edit_attempt(mock_callback, mock_state, lambda x: x)
                
                # Проверяем, что началось редактирование
                mock_start.assert_called_once()
                mock_callback.answer.assert_called_once()  # Без show_alert
    
    @pytest.mark.asyncio
    async def test_explain_protection(self, mock_callback):
        """Тест объяснения системы защиты"""
        await explain_field_protection(mock_callback, lambda x: x)
        
        call_args = mock_callback.message.edit_text.call_args
        message_text = call_args[0][0]
        
        assert "Field Protection System" in message_text
        assert "Why are some fields protected?" in message_text
        assert "What you can always edit:" in message_text
        assert "Monthly income" in message_text
        assert "Information about other loans" in message_text
    
    @pytest.mark.asyncio
    async def test_view_protected_data(self, mock_callback, mock_db, mock_user):
        """Тест просмотра защищенных данных"""
        personal_data = PersonalData(
            user_id=mock_user.id,
            age=30,
            gender=Gender.MALE,
            education=Education.HIGHER,
            housing_status=HousingStatus.OWN
        )
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await view_protected_data(mock_callback, lambda x: x)
            
            call_args = mock_callback.message.edit_text.call_args
            message_text = call_args[0][0]
            
            assert "Protected Data" in message_text
            assert "These fields cannot be changed:" in message_text
            assert "🔒" in message_text
            assert "30" in message_text  # Возраст
            assert "Male" in message_text  # Пол
            assert "Higher" in message_text  # Образование
            assert "Own property" in message_text  # Жилье
    
    @pytest.mark.asyncio
    async def test_show_editable_fields_menu(self, mock_callback, mock_db, mock_user):
        """Тест меню редактируемых полей"""
        personal_data = PersonalData(
            user_id=mock_user.id,
            age=30,  # Защищено
            monthly_income=100000  # Всегда редактируемо
        )
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await show_editable_fields_menu(mock_callback, lambda x: x)
            
            call_args = mock_callback.message.edit_text.call_args
            message_text = call_args[0][0]
            keyboard = call_args[1]['reply_markup']
            
            assert "Edit available fields" in message_text
            assert "Select a field to edit:" in message_text
            
            # Проверяем клавиатуру
            buttons = []
            for row in keyboard.inline_keyboard:
                for button in row:
                    buttons.append(button.text)
            
            # Доход должен быть в списке (с галочкой, так как заполнен)
            assert any("💰" in btn and "✅" in btn for btn in buttons)
            # Кнопка назад должна быть
            assert any("◀️" in btn for btn in buttons)
    
    @pytest.mark.asyncio
    async def test_keyboard_generation_with_protection(self):
        """Тест генерации клавиатуры с учетом защиты"""
        from src.bot.keyboards import Keyboards
        
        field_status = {
            'age': {'is_protected': True, 'is_filled': True, 'display_name': 'Age'},
            'gender': {'is_protected': True, 'is_filled': True, 'display_name': 'Gender'},
            'monthly_income': {'is_protected': False, 'is_filled': True, 'display_name': 'Monthly income'},
            'education': {'is_protected': False, 'is_filled': False, 'display_name': 'Education'}
        }
        
        keyboard = Keyboards.personal_data_menu_protected(field_status, lambda x: x)
        
        # Проверяем структуру клавиатуры
        buttons = []
        for row in keyboard.inline_keyboard:
            for button in row:
                buttons.append((button.text, button.callback_data))
        
        # Должны быть кнопки для редактирования и просмотра защищенных
        assert any("Edit available fields" in btn[0] for btn in buttons)
        assert any("View protected data (2)" in btn[0] for btn in buttons)
        assert any("Why are fields protected?" in btn[0] for btn in buttons)
    
    @pytest.mark.asyncio
    async def test_no_protected_fields_scenario(self, mock_callback, mock_db, mock_user):
        """Тест сценария без защищенных полей"""
        personal_data = PersonalData(user_id=mock_user.id)  # Все поля пустые
        
        mock_db.execute.return_value.scalar_one_or_none.side_effect = [mock_user, personal_data]
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            
            await view_protected_data(mock_callback, lambda x: x)
            
            # Должно показать уведомление, что нет защищенных полей
            mock_callback.answer.assert_called_with("No protected fields")