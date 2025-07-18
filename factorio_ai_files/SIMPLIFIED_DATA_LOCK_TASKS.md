# Упрощенный таск-лист: Блокировка обновления персональных данных

## Упрощенный подход

Вместо сложной системы с дополнительными полями в БД, используем **простую логику проверки заполненности полей**:

### Принцип работы:
1. **Проверка заполненности** - если поле уже заполнено (не NULL), то оно становится "заблокированным"
2. **UI блокировка** - пользователь не видит опций для изменения заполненных полей
3. **Исключения** - доход и кредитная информация всегда остаются редактируемыми
4. **Информирование** - объяснение пользователю, почему поле недоступно

## Преимущества упрощенного подхода:
- ✅ Нет изменений в БД
- ✅ Нет миграций
- ✅ Простая логика
- ✅ Быстрая реализация
- ✅ Легко тестировать

## Детальный план реализации

### Этап 1: Логика проверки заполненности (1 день)

#### 1.1 Создание утилиты проверки
**Файл:** `src/core/field_protection.py`

```python
from typing import List, Dict, Optional
from src.db.models import PersonalData
from src.core.enums import *

class FieldProtectionManager:
    """Менеджер защиты полей от изменения"""
    
    # Поля, которые блокируются после заполнения
    PROTECTED_FIELDS = {
        'age': 'Возраст',
        'gender': 'Пол',
        'work_experience_months': 'Стаж работы',
        'address_stability_years': 'Стабильность адреса',
        'housing_status': 'Статус жилья',
        'marital_status': 'Семейное положение',
        'education': 'Образование',
        'closed_loans_count': 'Количество закрытых займов',
        'region': 'Регион проживания',
        'device_type': 'Тип устройства'
    }
    
    # Поля, которые всегда можно редактировать
    ALWAYS_EDITABLE_FIELDS = {
        'monthly_income': 'Ежемесячный доход',
        'has_other_loans': 'Наличие других кредитов',
        'other_loans_monthly_payment': 'Платежи по другим кредитам'
    }
    
    @classmethod
    def is_field_protected(cls, personal_data: PersonalData, field_name: str) -> bool:
        """
        Проверяет, защищено ли поле от изменения
        
        Args:
            personal_data: Объект персональных данных
            field_name: Имя поля для проверки
            
        Returns:
            True если поле защищено (заполнено и не редактируемое)
        """
        # Всегда редактируемые поля никогда не защищены
        if field_name in cls.ALWAYS_EDITABLE_FIELDS:
            return False
            
        # Защищенные поля блокируются если заполнены
        if field_name in cls.PROTECTED_FIELDS:
            field_value = getattr(personal_data, field_name, None)
            return field_value is not None
            
        return False
    
    @classmethod
    def get_protected_fields(cls, personal_data: PersonalData) -> List[str]:
        """Возвращает список защищенных полей"""
        protected = []
        for field_name in cls.PROTECTED_FIELDS:
            if cls.is_field_protected(personal_data, field_name):
                protected.append(field_name)
        return protected
    
    @classmethod
    def get_editable_fields(cls, personal_data: PersonalData) -> List[str]:
        """Возвращает список полей доступных для редактирования"""
        editable = []
        
        # Всегда редактируемые поля
        editable.extend(cls.ALWAYS_EDITABLE_FIELDS.keys())
        
        # Незаполненные защищенные поля
        for field_name in cls.PROTECTED_FIELDS:
            if not cls.is_field_protected(personal_data, field_name):
                editable.append(field_name)
                
        return editable
    
    @classmethod
    def get_field_status(cls, personal_data: PersonalData) -> Dict[str, Dict[str, any]]:
        """
        Возвращает статус всех полей
        
        Returns:
            Dict с информацией о каждом поле:
            {
                'field_name': {
                    'is_protected': bool,
                    'is_filled': bool,
                    'display_name': str,
                    'current_value': any
                }
            }
        """
        status = {}
        
        all_fields = {**cls.PROTECTED_FIELDS, **cls.ALWAYS_EDITABLE_FIELDS}
        
        for field_name, display_name in all_fields.items():
            field_value = getattr(personal_data, field_name, None)
            
            status[field_name] = {
                'is_protected': cls.is_field_protected(personal_data, field_name),
                'is_filled': field_value is not None,
                'display_name': display_name,
                'current_value': field_value,
                'is_always_editable': field_name in cls.ALWAYS_EDITABLE_FIELDS
            }
            
        return status
    
    @classmethod
    def get_protection_reason(cls, field_name: str, translate=None) -> str:
        """Возвращает объяснение, почему поле защищено"""
        _ = translate if translate else lambda x: x
        
        if field_name in cls.PROTECTED_FIELDS:
            return _(
                "This field is protected because it's already filled and affects "
                "your credit score. This ensures the reliability of your assessment."
            )
        
        return _("This field is protected.")
```

### Этап 2: Модификация UI (1-2 дня)

#### 2.1 Обновление хендлера персональных данных
**Файл:** `src/bot/handlers/personal_data.py`

```python
from src.core.field_protection import FieldProtectionManager

@router.callback_query(F.data == "edit_personal_data")
async def show_personal_data_menu(callback: types.CallbackQuery, _: callable):
    """Показать меню редактирования персональных данных"""
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        # Получаем персональные данные пользователя
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user_id)
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
        await show_data_menu_with_protection(callback, field_status, _)

async def show_data_menu_with_protection(
    callback: types.CallbackQuery, 
    field_status: Dict[str, Dict[str, any]], 
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
            value = format_field_value(status['current_value'], field_name)
            icon = "🔒" if status['is_protected'] else "✅"
            message += f"{icon} {status['display_name']}: {value}\n"
    
    # Показываем доступные для редактирования
    if editable_fields:
        message += f"\n✏️ **{_('Available for editing')}:**\n"
        for field_name, status in editable_fields:
            if not status['is_filled']:
                message += f"📝 {status['display_name']}: {_('Not filled')}\n"
    
    # Информация о защищенных полях
    if protected_fields:
        message += f"\n🔒 **{_('Protected fields')}:** {len(protected_fields)}\n"
        message += f"💡 {_('These fields cannot be changed as they affect your credit score')}\n"
    
    await callback.message.edit_text(
        message,
        reply_markup=Keyboards.personal_data_menu_protected(field_status, _)
    )

def format_field_value(value: any, field_name: str) -> str:
    """Форматирует значение поля для отображения"""
    if value is None:
        return "Не заполнено"
    
    # Специальное форматирование для разных типов полей
    if field_name == 'gender':
        return "Мужской" if value == Gender.MALE else "Женский"
    elif field_name == 'monthly_income':
        return f"{value:,.0f} сум".replace(",", " ")
    elif field_name == 'has_other_loans':
        return "Да" if value else "Нет"
    elif field_name in ['work_experience_months', 'address_stability_years']:
        if field_name == 'work_experience_months':
            return f"{value} мес."
        else:
            return f"{value} лет"
    elif isinstance(value, Enum):
        return value.value.replace('_', ' ').title()
    
    return str(value)
```

#### 2.2 Обновление клавиатур
**Файл:** `src/bot/keyboards.py` (дополнение)

```python
@staticmethod
def personal_data_menu_protected(field_status: Dict[str, Dict[str, any]], translate=None):
    """Меню персональных данных с учетом защиты полей"""
    _ = translate if translate else lambda x: x
    
    keyboard = InlineKeyboardBuilder()
    
    # Кнопки для редактируемых полей
    editable_fields = [
        (name, status) for name, status in field_status.items() 
        if not status['is_protected']
    ]
    
    if editable_fields:
        keyboard.button(
            text=f"✏️ {_('Edit available fields')}",
            callback_data="edit_available_fields"
        )
    
    # Кнопка просмотра защищенных данных
    protected_count = sum(1 for s in field_status.values() if s['is_protected'])
    if protected_count > 0:
        keyboard.button(
            text=f"🔒 {_('View protected data')} ({protected_count})",
            callback_data="view_protected_data"
        )
    
    # Кнопка объяснения защиты
    if protected_count > 0:
        keyboard.button(
            text=f"❓ {_('Why are fields protected?')}",
            callback_data="explain_protection"
        )
    
    keyboard.button(text=f"◀️ {_('Back')}", callback_data="main_menu")
    keyboard.adjust(1)
    
    return keyboard.as_markup()

@staticmethod
def editable_fields_menu(field_status: Dict[str, Dict[str, any]], translate=None):
    """Меню редактируемых полей"""
    _ = translate if translate else lambda x: x
    
    keyboard = InlineKeyboardBuilder()
    
    # Добавляем кнопки только для редактируемых полей
    for field_name, status in field_status.items():
        if not status['is_protected']:
            icon = "💰" if field_name == 'monthly_income' else "📝"
            text = f"{icon} {status['display_name']}"
            
            if status['is_filled']:
                text += " ✅"
            
            keyboard.button(
                text=text,
                callback_data=f"edit_field:{field_name}"
            )
    
    keyboard.button(text=f"◀️ {_('Back')}", callback_data="edit_personal_data")
    keyboard.adjust(1)
    
    return keyboard.as_markup()
```

### Этап 3: Информационные сообщения (0.5 дня)

#### 3.1 Объяснение защиты полей
**Файл:** `src/bot/handlers/personal_data.py` (дополнение)

```python
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
        reply_markup=Keyboards.back_to_personal_data(_)
    )

@router.callback_query(F.data == "view_protected_data")
async def view_protected_data(callback: types.CallbackQuery, _: callable):
    """Показать защищенные данные"""
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user_id)
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
            value = format_field_value(status['current_value'], field_name)
            message += f"🔒 **{status['display_name']}**: {value}\n"
        
        message += f"\n💡 {_('These fields are locked because they affect your credit score.')}"
        
        await callback.message.edit_text(
            message,
            reply_markup=Keyboards.back_to_personal_data(_)
        )

@router.callback_query(F.data.startswith("edit_field:"))
async def handle_field_edit_attempt(callback: types.CallbackQuery, _: callable):
    """Обработка попытки редактирования поля"""
    field_name = callback.data.split(":")[1]
    user_id = callback.from_user.id
    
    async with get_db_context() as db:
        result = await db.execute(
            select(PersonalData).where(PersonalData.user_id == user_id)
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
        await start_field_editing(callback, field_name, personal_data, _)
```

### Этап 4: Тестирование (1 день)

#### 4.1 Unit тесты
**Файл:** `tests/unit/test_field_protection.py`

```python
import pytest
from src.core.field_protection import FieldProtectionManager
from src.db.models import PersonalData
from src.core.enums import Gender, Education, Region

class TestFieldProtectionManager:
    """Тесты менеджера защиты полей"""
    
    def test_is_field_protected_empty_field(self):
        """Тест: пустое поле не защищено"""
        personal_data = PersonalData()
        assert not FieldProtectionManager.is_field_protected(personal_data, 'age')
    
    def test_is_field_protected_filled_field(self):
        """Тест: заполненное защищаемое поле защищено"""
        personal_data = PersonalData(age=30)
        assert FieldProtectionManager.is_field_protected(personal_data, 'age')
    
    def test_is_field_protected_always_editable(self):
        """Тест: всегда редактируемое поле не защищено"""
        personal_data = PersonalData(monthly_income=100000)
        assert not FieldProtectionManager.is_field_protected(personal_data, 'monthly_income')
    
    def test_get_protected_fields_empty_data(self):
        """Тест: пустые данные - нет защищенных полей"""
        personal_data = PersonalData()
        protected = FieldProtectionManager.get_protected_fields(personal_data)
        assert protected == []
    
    def test_get_protected_fields_some_filled(self):
        """Тест: частично заполненные данные"""
        personal_data = PersonalData(
            age=30,
            gender=Gender.FEMALE,
            monthly_income=100000  # Всегда редактируемое
        )
        protected = FieldProtectionManager.get_protected_fields(personal_data)
        assert 'age' in protected
        assert 'gender' in protected
        assert 'monthly_income' not in protected
    
    def test_get_editable_fields(self):
        """Тест: получение редактируемых полей"""
        personal_data = PersonalData(
            age=30,  # Защищено
            monthly_income=100000  # Всегда редактируемо
        )
        editable = FieldProtectionManager.get_editable_fields(personal_data)
        
        # Доход всегда редактируемый
        assert 'monthly_income' in editable
        assert 'has_other_loans' in editable
        assert 'other_loans_monthly_payment' in editable
        
        # Возраст заполнен - не редактируемый
        assert 'age' not in editable
        
        # Пол не заполнен - редактируемый
        assert 'gender' in editable
    
    def test_get_field_status(self):
        """Тест: получение статуса всех полей"""
        personal_data = PersonalData(
            age=30,
            monthly_income=100000
        )
        status = FieldProtectionManager.get_field_status(personal_data)
        
        # Возраст защищен
        assert status['age']['is_protected'] is True
        assert status['age']['is_filled'] is True
        assert status['age']['current_value'] == 30
        
        # Доход не защищен
        assert status['monthly_income']['is_protected'] is False
        assert status['monthly_income']['is_filled'] is True
        assert status['monthly_income']['is_always_editable'] is True
        
        # Пол не заполнен
        assert status['gender']['is_protected'] is False
        assert status['gender']['is_filled'] is False
        assert status['gender']['current_value'] is None
    
    def test_get_protection_reason(self):
        """Тест: получение причины защиты"""
        reason = FieldProtectionManager.get_protection_reason('age')
        assert 'credit score' in reason.lower()
        assert 'reliability' in reason.lower()
```

#### 4.2 Integration тесты
**Файл:** `tests/integration/test_personal_data_protection.py`

```python
import pytest
from unittest.mock import AsyncMock, patch
from src.bot.handlers.personal_data import show_personal_data_menu
from src.core.field_protection import FieldProtectionManager
from src.db.models import PersonalData
from src.core.enums import Gender

class TestPersonalDataProtectionUI:
    """Тесты UI защиты персональных данных"""
    
    @pytest.mark.asyncio
    async def test_show_menu_with_empty_data(self, mock_callback, mock_db):
        """Тест отображения меню с пустыми данными"""
        personal_data = PersonalData()
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = personal_data
            
            await show_personal_data_menu(mock_callback, lambda x: x)
            
            # Проверяем, что сообщение содержит информацию о доступных полях
            call_args = mock_callback.message.edit_text.call_args
            message_text = call_args[0][0]
            
            assert "Available for editing" in message_text
            assert "Protected fields" not in message_text
    
    @pytest.mark.asyncio
    async def test_show_menu_with_protected_data(self, mock_callback, mock_db):
        """Тест отображения меню с защищенными данными"""
        personal_data = PersonalData(
            age=30,
            gender=Gender.FEMALE,
            monthly_income=100000
        )
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = personal_data
            
            await show_personal_data_menu(mock_callback, lambda x: x)
            
            call_args = mock_callback.message.edit_text.call_args
            message_text = call_args[0][0]
            
            assert "Protected fields" in message_text
            assert "🔒" in message_text
            assert "30" in message_text  # Возраст
    
    @pytest.mark.asyncio
    async def test_field_edit_attempt_protected(self, mock_callback, mock_db):
        """Тест попытки редактирования защищенного поля"""
        from src.bot.handlers.personal_data import handle_field_edit_attempt
        
        personal_data = PersonalData(age=30)
        mock_callback.data = "edit_field:age"
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = personal_data
            
            await handle_field_edit_attempt(mock_callback, lambda x: x)
            
            # Проверяем, что показано предупреждение
            mock_callback.answer.assert_called_once()
            call_args = mock_callback.answer.call_args
            assert "🔒" in call_args[0][0]
            assert call_args[1]['show_alert'] is True
    
    @pytest.mark.asyncio
    async def test_field_edit_attempt_editable(self, mock_callback, mock_db):
        """Тест попытки редактирования доступного поля"""
        from src.bot.handlers.personal_data import handle_field_edit_attempt
        
        personal_data = PersonalData(monthly_income=100000)
        mock_callback.data = "edit_field:monthly_income"
        
        with patch('src.bot.handlers.personal_data.get_db_context') as mock_get_db:
            mock_get_db.return_value.__aenter__.return_value = mock_db
            mock_db.execute.return_value.scalar_one_or_none.return_value = personal_data
            
            with patch('src.bot.handlers.personal_data.start_field_editing') as mock_start:
                await handle_field_edit_attempt(mock_callback, lambda x: x)
                
                # Проверяем, что началось редактирование
                mock_start.assert_called_once()
                mock_callback.answer.assert_not_called()
```

## Файловая структура упрощенного подхода

### Новые файлы:
```
src/core/field_protection.py                   # Логика защиты полей (простая)
tests/unit/test_field_protection.py            # Unit тесты
tests/integration/test_personal_data_protection.py  # Integration тесты
```

### Модифицируемые файлы:
```
src/bot/handlers/personal_data.py              # UI с защитой полей
src/bot/keyboards.py                           # Новые клавиатуры
```

## Сравнение подходов

### Сложный подход (с БД):
- ❌ Миграция БД
- ❌ Дополнительные поля
- ❌ Сложная логика
- ✅ Полный audit trail
- ✅ Гибкие правила блокировки

### Упрощенный подход:
- ✅ Без изменений БД
- ✅ Простая логика
- ✅ Быстрая реализация
- ✅ Легко тестировать
- ❌ Нет audit trail
- ❌ Менее гибкие правила

## Временная оценка упрощенного подхода

**Общее время:** 2-3 дня
- Этап 1 (Логика): 1 день
- Этап 2 (UI): 1-2 дня  
- Этап 3 (Сообщения): 0.5 дня
- Этап 4 (Тесты): 1 день

## Критерии готовности

### Функциональные требования:
- [ ] Заполненные поля (кроме исключений) нельзя редактировать
- [ ] Пользователь видит статус полей (защищено/доступно)
- [ ] Доход и кредитная информация всегда редактируемы
- [ ] Есть объяснение системы защиты
- [ ] Попытки редактирования защищенных полей блокируются с объяснением

### Технические требования:
- [ ] Unit тесты покрывают >95% логики защиты
- [ ] Integration тесты проверяют UI
- [ ] Нет регрессии в существующем функционале
- [ ] Производительность не ухудшается

## Вывод

Упрощенный подход **значительно проще** в реализации и достигает той же цели - предотвращение изменения данных после их использования в скоринге. Основное преимущество - отсутствие изменений в БД и быстрая реализация.