# KreditScore Bot

Telegram-бот для оценки долговой нагрузки и скоринга пользователей с возможностью подачи заявок на кредиты.

## Функциональность

- 📊 Расчет показателя долговой нагрузки (ПДН)
- 🎯 Скоринг-система на основе персональных данных
- 💳 Подача заявок на автокредиты и микрозаймы
- 🎁 Реферальная программа
- 🏦 Симуляция отправки заявок в банки
- 🌐 Поддержка русского и узбекского языков

## Технологии

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Bot**: Aiogram 3.3
- **Database**: PostgreSQL
- **Deployment**: Railway
- **CI/CD**: GitHub Actions

## Установка и запуск

### Локальная разработка

1. Клонируйте репозиторий:
```bash
git clone https://github.com/yourusername/kreditscore-bot.git
cd kreditscore-bot
```

2. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\\Scripts\\activate  # Windows
```

3. Установите зависимости:
```bash
pip install -r requirements.txt
```

4. Скопируйте и настройте переменные окружения:
```bash
cp .env.example .env
# Отредактируйте .env файл
```

5. Запустите через Docker Compose:
```bash
docker-compose up -d
```

6. Примените миграции:
```bash
alembic upgrade head
```

7. Запустите бота:
```bash
python -m src.bot.main
```

### Деплой на Railway

1. Создайте проект на [Railway](https://railway.app)
2. Подключите GitHub репозиторий
3. Добавьте PostgreSQL сервис
4. Настройте переменные окружения
5. Деплой произойдет автоматически

## Структура проекта

```
src/
├── bot/             # Telegram bot хендлеры и логика
├── core/            # Бизнес-логика (ПДН, скоринг, рефералы)
├── api/             # FastAPI эндпоинты
├── db/              # Модели и миграции базы данных
└── config/          # Настройки приложения
```

## API эндпоинты

- `POST /api/v1/calculate/pdn` - Расчет ПДН
- `POST /api/v1/calculate/scoring` - Расчет скоринга
- `GET /api/v1/users/{telegram_id}/applications` - Получение заявок пользователя

## Команды бота

- `/start` - Начать работу с ботом
- `/menu` - Главное меню
- `/my_app` - Моя текущая заявка
- `/invite` - Реферальная программа
- `/help` - Справка

## Тестирование

```bash
# Запуск всех тестов
pytest

# С покрытием
pytest --cov=src

# Только unit тесты
pytest tests/unit/
```

## Лицензия

MIT