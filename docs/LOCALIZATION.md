# Локализация KreditScore Bot

## Поддерживаемые языки
- 🇷🇺 Русский (ru) - основной язык
- 🇺🇿 Узбекский (uz) - латиница

## Структура системы локализации

### Основные компоненты

1. **Система i18n** (`src/bot/i18n.py`)
   - Функция `simple_gettext()` для получения переводов
   - Middleware для автоматического определения языка пользователя
   - Загрузка переводов из .po файлов и встроенного словаря

2. **Файлы переводов**
   - `src/bot/i18n/ru.po` - русские переводы
   - `src/bot/i18n/uz.po` - узбекские переводы
   - Более 500 переведенных строк в каждом файле

3. **Поддержка в модулях**
   - Все handler'ы получают функцию перевода `_` через параметр
   - Core модули поддерживают опциональный параметр `translate`
   - Keyboards динамически переводят все тексты

## Использование в коде

### В handler'ах бота

```python
@router.message(Command("help"))
async def show_help(message: types.Message, _: callable):
    # Используем функцию _ для перевода
    help_text = f"""
    📚 **{_('Bot Usage Guide')}**
    
    **{_('Main commands')}:**
    /start - {_('Start using the bot')}
    """
    await message.answer(help_text)
```

### В core модулях

```python
# Core модули поддерживают опциональный параметр translate
def validate_loan_parameters(
    loan_type: LoanType, 
    amount: Decimal, 
    rate: Decimal, 
    term_months: int,
    translate: Optional[Callable[[str], str]] = None
) -> Dict[str, Any]:
    if amount <= 0:
        msg = translate('Loan amount must be positive') if translate else 'Loan amount must be positive'
        errors.append(msg)
```

### В клавиатурах

```python
@staticmethod
def region_choice(_: Callable[[str], str]) -> InlineKeyboardMarkup:
    regions = [
        (_('Tashkent'), Region.TASHKENT.value),
        (_('Andijan'), Region.ANDIJAN.value),
        # ...
    ]
```

## Добавление новых переводов

### 1. Добавить в .po файлы

```po
# В src/bot/i18n/ru.po
msgid "New feature"
msgstr "Новая функция"

# В src/bot/i18n/uz.po
msgid "New feature"  
msgstr "Yangi funksiya"
```

### 2. Использовать в коде

```python
# В handler'е
text = _('New feature')

# В core модуле
text = translate('New feature') if translate else 'New feature'
```

## Форматирование строк

Для строк с параметрами используется метод `.format()`:

```python
# В .po файле
msgid "Welcome, {name}!"
msgstr "Добро пожаловать, {name}!"

# В коде
welcome_text = _('Welcome, {name}!').format(name=user_name)
```

## Тестирование локализации

### Запуск тестов

```bash
# Все тесты локализации
pytest tests/unit/test_i18n_completeness.py -v

# Проверка полноты переводов
pytest tests/unit/test_i18n_completeness.py::TestI18nCompleteness -v

# Проверка отсутствия хардкода
pytest tests/unit/test_i18n_completeness.py::TestHardcodedStringsRemoved -v
```

### Что проверяется

1. **Полнота переводов**
   - Все ключи из русского языка есть в узбекском
   - Все ключи из узбекского есть в русском
   - Нет пустых переводов

2. **Консистентность**
   - Форматные строки имеют одинаковые плейсхолдеры
   - .po файлы валидны и содержат одинаковое количество записей

3. **Отсутствие хардкода**
   - В handler'ах нет русских строк
   - В keyboards нет названий регионов
   - В core модулях нет сообщений об ошибках

## Компиляция переводов (опционально)

Для ускорения загрузки можно скомпилировать .po файлы в .mo:

```bash
# Установить gettext tools
apt-get install gettext  # Ubuntu/Debian
brew install gettext      # macOS

# Компиляция
msgfmt src/bot/i18n/ru.po -o src/bot/i18n/ru.mo
msgfmt src/bot/i18n/uz.po -o src/bot/i18n/uz.mo
```

## Рекомендации

1. **Всегда добавляйте переводы в оба языка**
   - При добавлении нового текста сразу добавляйте в ru.po и uz.po

2. **Используйте понятные ключи**
   - Плохо: `msgid "msg1"`
   - Хорошо: `msgid "Welcome message"`

3. **Сохраняйте контекст**
   - Добавляйте комментарии в .po файлы для сложных переводов
   - Группируйте связанные переводы

4. **Тестируйте переводы**
   - Проверяйте оба языка после изменений
   - Запускайте тесты локализации

5. **Поддерживайте консистентность**
   - Используйте одинаковую терминологию
   - Следите за стилем переводов

## Структура переводов

### Основные категории

1. **Общие элементы UI**
   - Кнопки навигации (Back, Cancel, Next)
   - Меню и настройки
   - Сообщения об ошибках

2. **Кредитная заявка**
   - Типы кредитов
   - Параметры кредита
   - Расчет ПДН

3. **Персональные данные**
   - Вопросы анкеты
   - Названия полей
   - Регионы

4. **Скоринг**
   - Критерии оценки
   - Уровни скоринга
   - Детализация баллов

5. **Валидация**
   - Сообщения об ошибках
   - Ограничения параметров
   - Подсказки пользователю

## Отладка

### Проверка текущего языка пользователя

```python
# В handler'е
user_lang = await get_user_language(db, message.from_user.id)
print(f"User language: {user_lang}")
```

### Проверка загруженных переводов

```python
from src.bot.i18n import TRANSLATIONS
print(f"Loaded languages: {list(TRANSLATIONS.keys())}")
print(f"Russian keys: {len(TRANSLATIONS['ru'])}")
print(f"Uzbek keys: {len(TRANSLATIONS['uz'])}")
```

### Логирование переводов

```python
# Включить в i18n.py для отладки
def simple_gettext(lang_code: str, message: str) -> str:
    logger.debug(f"Translating '{message}' to {lang_code}")
    # ...
```

## Часто используемые переводы

| Ключ | Русский | Узбекский |
|------|---------|-----------|
| Back | Назад | Orqaga |
| Cancel | Отмена | Bekor qilish |
| Main menu | Главное меню | Asosiy menyu |
| Settings | Настройки | Sozlamalar |
| Yes | Да | Ha |
| No | Нет | Yo'q |
| sum | сум | so'm |
| months | месяцев | oy |

## Расширение системы

### Добавление нового языка

1. Создать новый .po файл:
   ```bash
   cp src/bot/i18n/ru.po src/bot/i18n/en.po
   ```

2. Обновить i18n.py:
   ```python
   SUPPORTED_LANGUAGES = ['ru', 'uz', 'en']
   ```

3. Перевести все строки в новом .po файле

4. Обновить клавиатуру выбора языка

5. Добавить тесты для нового языка

### Интеграция с внешними сервисами

Система поддерживает загрузку переводов из:
- .po/.mo файлов (gettext)
- Встроенного словаря Python
- Внешних API (требует модификации)
- Базы данных (требует модификации)

## Производительность

- Переводы кешируются в памяти при запуске
- Нет обращений к диску при каждом переводе
- Минимальный overhead на перевод (~0.001ms)
- Поддержка компилированных .mo файлов для еще большей скорости