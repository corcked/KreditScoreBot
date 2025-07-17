# Таск-лист для реализации KreditScore Bot

## Общая информация о проекте
**Проект:** KreditScore - сервис оценки долговой нагрузки и скоринга пользователей  
**Интерфейс:** Telegram-бот  
**Стек:** Python, FastAPI, PostgreSQL, Aiogram v3, Railway  
**Продолжительность:** 9 недель  

## Детальный план реализации

### 1. Настройка инфраструктуры и окружения (1 неделя)

#### 1.1 Создание структуры проекта
**Файлы для создания:**
```
src/
├── bot/
│   ├── main.py                  # webhook handler
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── onboarding.py       # регистрация пользователей
│   │   ├── loan.py             # создание/просмотр заявок
│   │   ├── personal_data.py    # сбор персональных данных
│   │   ├── referral.py         # реферальная программа
│   │   └── bank_flow.py        # отправка в банк
│   ├── middleware/
│   │   └── rate_limit.py       # защита от спама
│   └── i18n/
│       ├── ru.po
│       └── uz.po
├── core/
│   ├── __init__.py
│   ├── pdn.py                  # расчет ПДН
│   ├── scoring.py              # скоринг формула
│   ├── referral.py             # реферальная логика
│   └── enums.py                # константы и перечисления
├── api/
│   ├── __init__.py
│   └── router.py               # FastAPI роутер
├── db/
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy модели
│   ├── repository.py           # репозиторий паттерн
│   └── migrations/             # Alembic миграции
├── config/
│   ├── __init__.py
│   ├── settings.py             # настройки приложения
│   └── logging.yaml            # конфигурация логирования
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── test_pdn.py
    │   ├── test_scoring.py
    │   └── test_referral.py
    ├── integration/
    │   ├── test_bot_flows.py
    │   └── test_api.py
    └── e2e/
        └── test_telegram_scenarios.py
```

#### 1.2 Настройка окружения
**Файлы для создания:**
- `requirements.txt` - зависимости Python
- `docker-compose.yml` - для локальной разработки
- `Dockerfile` - для контейнеризации
- `.env.example` - пример переменных окружения
- `.github/workflows/ci.yml` - CI/CD pipeline

### 2. Реализация core модулей (2 недели)

#### 2.1 Модуль расчета ПДН (`src/core/pdn.py`)
**Основные функции:**
- `calculate_annuity_payment(amount, rate, months)` - расчет аннуитетного платежа
- `calculate_pdn(monthly_payment, monthly_income, other_payments=0)` - расчет ПДН
- `get_pdn_status(pdn_value)` - статус ПДН (зеленый/желтый/красный)

**Тесты:** `tests/unit/test_pdn.py`

#### 2.2 Модуль скоринга (`src/core/scoring.py`)
**Основные функции:**
- `calculate_base_score(personal_data)` - базовый скоринг
- `add_referral_bonus(score, referral_count)` - бонус за рефералы
- `clamp_score(score)` - ограничение 300-900
- `get_scoring_breakdown(data)` - детализация баллов

**Тесты:** `tests/unit/test_scoring.py`

#### 2.3 Модуль рефералов (`src/core/referral.py`)
**Основные функции:**
- `generate_referral_link(user_id)` - генерация ссылки
- `validate_referral_code(code)` - валидация кода
- `process_referral_registration(referrer_id, new_user_id)` - обработка регистрации

**Тесты:** `tests/unit/test_referral.py`

### 3. Настройка базы данных (1 неделя)

#### 3.1 Модели данных (`src/db/models.py`)
**Основные модели:**
- `User` - пользователи
- `LoanApplication` - заявки на займы
- `PersonalData` - персональные данные
- `ReferralLink` - реферальные ссылки
- `ReferralRegistration` - регистрации по рефералам

#### 3.2 Миграции (`src/db/migrations/`)
**Alembic миграции:**
- `001_initial_schema.py` - начальная схема
- `002_add_referral_system.py` - реферальная система
- `003_add_bank_flow.py` - статусы отправки в банк

**Тесты:** `tests/integration/test_models.py`

### 4. Реализация Telegram бота (2 недели)

#### 4.1 Основные хендлеры
**`src/bot/handlers/onboarding.py`:**
- Команда `/start` - приветствие
- Обработка deep-link рефералов
- Получение контакта пользователя

**`src/bot/handlers/loan.py`:**
- Создание заявки на займ
- Выбор типа кредита (автокредит/микрозайм)
- Команда `/my_app` - просмотр заявки
- Архивация старых заявок

**`src/bot/handlers/personal_data.py`:**
- Wizard-форма для сбора данных
- Inline-кнопки для выбора
- Обновление скоринга в реальном времени

**`src/bot/handlers/referral.py`:**
- Команда `/invite` - получение ссылки
- Отображение статистики рефералов

**`src/bot/handlers/bank_flow.py`:**
- Кнопка "Отправить в банк"
- Cron-job эмуляции ответа банка
- Уведомления о статусе

#### 4.2 FSM машины состояний
**Состояния для автокредита:**
- `LoanType` → `CarCondition` → `Amount` → `Rate` → `Term` → `Income`

**Состояния для микрозайма:**
- `LoanType` → `ReceiveMethod` → `Amount` → `Rate` → `Term` → `Income`

**Тесты:** `tests/integration/test_bot_flows.py`

### 5. Локализация (1 неделя)

#### 5.1 Файлы переводов
**`src/bot/i18n/ru.po`** - русский язык
**`src/bot/i18n/uz.po`** - узбекский (латиница)

#### 5.2 Интеграция с gettext
- Функция `_()` для переводов
- Middleware для определения языка
- Inline-кнопки смены языка

### 6. Тестирование (1 неделя)

#### 6.1 Unit тесты
**`tests/unit/`:**
- `test_pdn.py` - тесты расчета ПДН
- `test_scoring.py` - тесты скоринга
- `test_referral.py` - тесты рефералов
- **Coverage:** ≥95%

#### 6.2 Integration тесты
**`tests/integration/`:**
- `test_bot_flows.py` - FSM переходы
- `test_api.py` - FastAPI эндпоинты
- `test_models.py` - работа с БД

#### 6.3 E2E тесты
**`tests/e2e/`:**
- `test_telegram_scenarios.py` - полные сценарии
- Использование `pytest-telethon`
- Тесты для двух языков

### 7. Безопасность и мониторинг (1 неделя)

#### 7.1 Безопасность
- Rate limiting middleware
- Валидация входных данных
- Защита от SQL-инъекций
- Bandit/Semgrep в CI

#### 7.2 Мониторинг
- Prometheus метрики
- Grafana Cloud dashboard
- Алерты на ошибки >1%
- Логирование всех операций

### 8. CI/CD и деплой (1 неделя)

#### 8.1 GitHub Actions
**`.github/workflows/ci.yml`:**
- Запуск тестов
- Линтинг (flake8)
- Проверка миграций
- Сборка Docker образа
- Деплой на Railway

#### 8.2 Railway настройка
- Staging и Production окружения
- Переменные окружения
- Автоматический деплой из main ветки
- Backup БД

## Бизнес-правила и ограничения

### Типы кредитов
**Автокредит:**
- Сумма: до 1,000,000,000 сум
- Ставка: 4-48%
- Срок: 6 месяцев - 5 лет
- Дополнительно: новый/б/у автомобиль

**Микрозайм:**
- Сумма: до 100,000,000 сум
- Ставка: 18-79%
- Срок: 1 месяц - 3 года
- Дополнительно: на карту/наличными

### Скоринг баллы
- Возраст ≥35 лет: +70
- Женский пол: +20
- Стаж ≥24 мес: +20
- Адрес ≥3 года: +30
- Собственное жилье: +20
- Женат/замужем: +10
- Высшее образование: +20
- Закрытые займы ≥3: +20
- Другие платежи (ПДН ≤50%): +30
- Ташкент: +20
- Apple устройство: +20
- Реферал: +20

### Формулы
- **ПДН** = (Ежемесячные платежи / Доход) × 100%
- **Скоринг** = CLAMP(600 + Σ баллы, 300, 900)
- **Аннуитет** = P × [r(1+r)^n] / [(1+r)^n - 1]

## Критерии готовности
- [ ] Все unit тесты проходят (coverage ≥95%)
- [ ] Integration тесты проходят
- [ ] E2E сценарии работают
- [ ] Локализация RU/UZ работает
- [ ] Реферальная система функционирует
- [ ] ПДН рассчитывается корректно
- [ ] Скоринг обновляется в реальном времени
- [ ] Статусы заявок корректно обрабатываются
- [ ] CI/CD пайплайн настроен
- [ ] Мониторинг и алерты работают
- [ ] Документация обновлена

## Команда и роли
- **Backend разработчик** - core модули, API
- **Bot разработчик** - Telegram интерфейс
- **DevOps** - инфраструктура, CI/CD
- **QA** - тестирование, автотесты
- **PM** - координация, требования