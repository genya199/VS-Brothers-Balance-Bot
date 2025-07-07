# 🚀 Швидкий гайд налаштування Supabase

## 1. Створення Supabase проекту

1. Відкрийте [supabase.com](https://supabase.com) та зареєструйтеся
2. Натисніть **"New project"**
3. Виберіть організацію та введіть:
   - **Name**: `car-payments-bot` (або будь-яка назва)
   - **Database Password**: запам'ятайте пароль
   - **Region**: оберіть найближчий регіон
4. Натисніть **"Create new project"**
5. Дочекайтеся завершення створення (2-3 хвилини)

## 2. Налаштування бази даних

1. У лівому меню оберіть **"SQL Editor"**
2. Натисніть **"New query"**
3. Скопіюйте весь вміст файлу `supabase_setup.sql` та вставте в редактор
4. Натисніть **"Run"** або `Ctrl+Enter`
5. Переконайтеся, що всі команди виконалися без помилок

## 3. Отримання API ключів

1. У лівому меню оберіть **"Settings"**
2. Оберіть **"API"**
3. Скопіюйте:
   - **Project URL** (наприклад: `https://abcdefgh.supabase.co`)
   - **anon public** ключ (наприклад: `eyJhbGciOiJIUzI1NiIs...`)

## 4. Налаштування бота

1. Скопіюйте `bot_config_example.txt` як `bot_config.env`:
   ```bash
   cp bot_config_example.txt bot_config.env
   ```

2. Відредагуйте `bot_config.env`:
   ```env
   BOT_TOKEN=ваш_токен_від_BotFather
   SUPABASE_URL=https://abcdefgh.supabase.co
   SUPABASE_KEY=eyJhbGciOiJIUzI1NiIs...
   ```

## 5. Встановлення залежностей та запуск

```bash
# Встановлення залежностей
pip install -r requirements.txt

# Запуск бота
python main.py
```

## 6. Тестування підключення

Перед запуском бота протестуйте підключення:

```bash
python test_supabase.py
```

Якщо все налаштовано правильно, ви побачите:
```
🎉 Всі тести пройшли успішно!
✅ Supabase готовий до роботи
🚀 Можете запускати бота: python main.py
```

## 7. Запуск бота

```bash
python main.py
```

У логах ви побачите:
```
INFO - Підключення до Supabase успішно встановлено
INFO - Бот запущено успішно
```

## ✅ Готово!

Тепер ваш бот готовий до роботи з Supabase!

## ❗ Типові помилки

### `ValueError: SUPABASE_URL та SUPABASE_KEY мають бути встановлені`
- Перевірте, що файл `bot_config.env` існує
- Перевірте правильність змінних у файлі

### `relation "invoices" does not exist`
- Переконайтеся, що ви виконали SQL команди з `supabase_setup.sql`
- Перевірте в Supabase Dashboard → Table Editor, що таблиці створені

### Бот не відповідає
- Перевірте токен бота в `bot_config.env`
- Перевірте логи у файлі `bot.log`

## 📞 Підтримка

Якщо виникли проблеми:
1. Перевірте логи в `bot.log`
2. Перевірте статус Supabase проекту в Dashboard
3. Переконайтеся, що всі змінні середовища встановлені правильно 