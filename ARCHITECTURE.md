# 🏗️ Архітектура проекту

Документація для розробників, які хочуть зрозуміти устрій бота.

## 📋 Огляд

Telegram бот для обліку платежів за перевезення автомобілів, побудований на:
- **aiogram 3.x** - асинхронний фреймворк для Telegram ботів
- **Supabase** - Backend-as-a-Service з PostgreSQL
- **FSM (Finite State Machine)** - управління станами діалогу

## 🧩 Компоненти

### 📁 Основні модулі

#### `main.py`
- **Призначення**: Точка входу, основна логіка бота
- **Відповідальність**: 
  - Ініціалізація бота та диспетчера
  - Обробники команд та колбеків
  - Машина станів (FSM)
- **Ключові функції**:
  - `cmd_start()` - обробка команди /start
  - `process_invoice_text()` - парсинг рахунків
  - `process_payment_amount()` - обробка платежів

#### `supabase_database.py`
- **Призначення**: Абстракція роботи з базою даних
- **Відповідальність**:
  - CRUD операції з рахунками, платежами, балансом
  - Управління підключенням до Supabase
- **Ключові методи**:
  - `add_invoice()` / `add_payment()` - додавання записів
  - `get_balance()` / `get_history()` - отримання даних
  - `delete_*()` - видалення операцій

#### `keyboards.py`
- **Призначення**: Інтерфейс користувача (Inline клавіатури)
- **Відповідальність**:
  - Генерація кнопок для різних меню
  - Календар для вибору дат
  - Навігація по сторінках
- **Ключові функції**:
  - `get_main_menu()` - головне меню
  - `get_calendar()` - інтерактивний календар
  - `get_history_keyboard()` - навігація історії

#### `utils.py`
- **Призначення**: Допоміжні функції та утиліти
- **Відповідальність**:
  - Парсинг сум з тексту
  - Витягування інформації про авто
  - Форматування дат та валют
- **Ключові функції**:
  - `parse_amount_from_text()` - розпізнавання сум
  - `extract_car_info()` - витягування даних авто
  - `validate_amount()` - валідація введених сум

#### `config.py`
- **Призначення**: Конфігурація та константи
- **Відповідальність**:
  - Змінні середовища
  - Тексти повідомлень
  - Налаштування форматів

### 🔧 Допоміжні файли

#### `test_supabase.py`
- **Призначення**: Тестування підключення до Supabase
- **Використання**: Перевірка налаштувань перед запуском

#### `supabase_setup.sql`
- **Призначення**: SQL скрипт для створення таблиць
- **Використання**: Ініціалізація бази даних в Supabase

## 🗄️ Модель даних

### Таблиці

#### `invoices` (рахунки)
```sql
id BIGSERIAL PRIMARY KEY
user_id BIGINT NOT NULL          -- Telegram ID користувача
car_info TEXT NOT NULL           -- Інформація про авто (модель, VIN)
amount DECIMAL(10,2) NOT NULL    -- Сума рахунку
original_text TEXT NOT NULL      -- Оригінальний текст повідомлення
date_created TIMESTAMP           -- Дата створення
```

#### `payments` (платежі)
```sql
id BIGSERIAL PRIMARY KEY
user_id BIGINT NOT NULL          -- Telegram ID користувача
amount DECIMAL(10,2) NOT NULL    -- Сума платежу
date_paid TEXT NOT NULL          -- Дата платежу (DD.MM.YYYY)
date_created TIMESTAMP           -- Дата створення запису
```

#### `balance` (баланси)
```sql
user_id BIGINT PRIMARY KEY       -- Telegram ID користувача
current_balance DECIMAL(10,2)    -- Поточний баланс (+ переплата, - борг)
last_updated TIMESTAMP           -- Остання дата оновлення
```

### Зв'язки

- **Один користувач** → **багато рахунків** (1:N)
- **Один користувач** → **багато платежів** (1:N)  
- **Один користувач** → **один баланс** (1:1)

## 🔄 Потік даних

### Додавання рахунку
```
1. Користувач надсилає текст повідомлення від компанії
2. parse_amount_from_text() витягує суму
3. extract_car_info() розпізнає інформацію про авто
4. add_invoice() додає запис до БД
5. _update_balance() віднімає суму з балансу
6. Відправка підтвердження користувачу
```

### Додавання платежу
```
1. Користувач вводить суму платежу
2. validate_amount() перевіряє коректність
3. Користувач обирає дату в календарі
4. add_payment() додає запис до БД
5. _update_balance() додає суму до балансу
6. Відправка підтвердження користувачу
```

### Відображення історії
```
1. get_history() отримує операції з БД
2. Об'єднання рахунків та платежів
3. Сортування по даті (найновіші спочатку)
4. Пагінація результатів
5. Генерація клавіатури з навігацією
```

## 🚀 Масштабованість

### Поточні обмеження
- **Одноразове користування**: Один користувач = один потік операцій
- **Синхронні операції**: Операції виконуються послідовно
- **Пам'ять**: FSM стани зберігаються в `MemoryStorage`

### Потенційні покращення
1. **Redis storage** для FSM станів
2. **Connection pooling** для Supabase
3. **Кешування** запитів через Redis
4. **Batch операції** для масових імпортів
5. **Rate limiting** для захисту від спаму

## 🔒 Безпека

### Поточні заходи
- **Environment variables** для секретів
- **Row Level Security** в Supabase (опціонально)
- **Валідація введених даних**
- **Логування операцій**

### Рекомендації для продакшену
1. **HTTPS-only** для webhooks
2. **Whitelist користувачів** (якщо потрібно)
3. **Backup стратегія** для Supabase
4. **Моніторинг** помилок та метрик
5. **Rate limiting** на рівні Telegram API

## 🧪 Тестування

### Поточні тести
- `test_supabase.py` - перевірка підключення до БД

### Потенційні тести
```python
# Unit тести
test_parse_amount_from_text()
test_extract_car_info()
test_validate_amount()

# Integration тести  
test_add_invoice_flow()
test_add_payment_flow()
test_balance_calculation()

# E2E тести
test_full_user_journey()
```

## 📊 Моніторинг

### Рекомендовані метрики
- **Кількість користувачів** (DAU/MAU)
- **Кількість операцій** (рахунки/платежі на день)
- **Час відповіді** API запитів
- **Помилки** та exception rate
- **Використання БД** (storage, запити)

### Логування
```python
# Поточне логування
logger.info(f"Рахунок додано для користувача {user_id}")
logger.error(f"Помилка додавання рахунку: {e}")

# Структуроване логування (рекомендація)
logger.info("invoice_added", extra={
    "user_id": user_id,
    "amount": amount,
    "car_info": car_info
})
```

## 🔧 Deployment

### Development
```bash
python main.py  # Локальний запуск
```

### Production (Heroku)
```bash
heroku ps:scale worker=1  # Запуск worker dyno
```

### Environment Variables
```bash
BOT_TOKEN=telegram_bot_token
SUPABASE_URL=https://project.supabase.co
SUPABASE_KEY=supabase_anon_key
```

## 🔮 Майбутні можливості

### Функціональні
- **Експорт в Excel/PDF**
- **Статистика та аналітика**
- **Нотифікації про борги**
- **Інтеграція з платіжними системами**
- **Мульти-валютність**

### Технічні
- **Веб-інтерфейс** (Django/FastAPI)
- **API endpoints** для інтеграцій
- **Webhook замість polling**
- **Microservices архітектура**
- **GraphQL API** через Supabase 