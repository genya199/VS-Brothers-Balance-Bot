# ⚡ Швидкий старт

Найпростіший спосіб запустити бота за 5 хвилин.

## 🎯 Що потрібно

- Акаунт [Supabase](https://supabase.com) (безкоштовний)
- Токен Telegram бота від [@BotFather](https://t.me/BotFather)
- Python 3.8+ на вашому комп'ютері

## 🚀 5 простих кроків

### 1️⃣ Створіть Supabase проект
- Зайдіть на [supabase.com](https://supabase.com)
- Натисніть "New project" 
- Виберіть назву та регіон
- Дочекайтеся створення (2-3 хв)

### 2️⃣ Налаштуйте базу даних
- Відкрийте **SQL Editor** в Supabase
- Скопіюйте весь вміст файлу `supabase_setup.sql`
- Вставте в редактор та натисніть **Run**

### 3️⃣ Отримайте ключі
- Перейдіть в **Settings** → **API**
- Скопіюйте:
  - **Project URL** 
  - **anon public** ключ

### 4️⃣ Налаштуйте бота
```bash
# Скопіюйте приклад конфігурації
cp bot_config_example.txt bot_config.env

# Відредагуйте bot_config.env та вставте ваші дані:
# BOT_TOKEN=ваш_токен_від_BotFather
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_KEY=ваш_ключ
```

### 5️⃣ Запустіть бота
```bash
# Встановіть залежності
pip install -r requirements.txt

# Протестуйте підключення
python test_supabase.py

# Запустіть бота
python main.py
```

## ✅ Готово!

Якщо все пройшло успішно, ви побачите:
```
INFO - Підключення до Supabase успішно встановлено
INFO - Бот запущено успішно
```

Тепер знайдіть вашого бота в Telegram та напишіть `/start`!

## 🆘 Проблеми?

- **Помилка підключення** → перевірте URL та ключ в `bot_config.env`
- **Таблиці не знайдено** → переконайтеся, що виконали `supabase_setup.sql`
- **Бот не відповідає** → перевірте токен бота

📖 Детальні інструкції в `SETUP_GUIDE.md` 