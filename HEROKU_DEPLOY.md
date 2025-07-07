# 🚀 Деплой бота на Heroku з Supabase

## Переваги такого підходу

- **☁️ Повністю хмарний** - і бот, і база даних в хмарі
- **📈 Масштабованість** - автоматичне масштабування при зростанні навантаження
- **💰 Економічність** - безкоштовні рівні для початку
- **🔄 Надійність** - автоматичні бекапи та відновлення

## Підготовка

1. **Налаштуйте Supabase** (див. `SETUP_GUIDE.md`)
2. **Створіть акаунт на [Heroku](https://heroku.com)**
3. **Встановіть Heroku CLI** ([інструкції](https://devcenter.heroku.com/articles/heroku-cli))

## Крок 1: Підготовка коду

```bash
# Клонуйте репозиторій (якщо ще не зробили)
git clone <your-repo-url>
cd vs-brothers-bot

# Переконайтеся, що у вас є необхідні файли:
ls -la
# Повинні бути: Procfile, requirements.txt, runtime.txt, supabase_database.py
```

## Крок 2: Створення Heroku застосунку

```bash
# Увійдіть в Heroku
heroku login

# Створіть новий застосунок
heroku create your-bot-name

# Або якщо застосунок вже існує
heroku git:remote -a your-existing-app-name
```

## Крок 3: Налаштування змінних середовища

Встановіть змінні середовища через Heroku CLI:

```bash
# Токен бота
heroku config:set BOT_TOKEN=your_bot_token_here

# Дані Supabase
heroku config:set SUPABASE_URL=https://your-project.supabase.co
heroku config:set SUPABASE_KEY=your_supabase_anon_key
```

Або через веб-інтерфейс:
1. Відкрийте https://dashboard.heroku.com/apps/your-app-name
2. Перейдіть до **Settings**
3. Натисніть **"Reveal Config Vars"**
4. Додайте змінні:
   - `BOT_TOKEN` = ваш токен від BotFather
   - `SUPABASE_URL` = URL вашого Supabase проекту
   - `SUPABASE_KEY` = anon ключ з Supabase

## Крок 4: Деплой

```bash
# Додайте зміни до git (якщо потрібно)
git add .
git commit -m "Add Supabase support"

# Деплой на Heroku
git push heroku main
```

## Крок 5: Запуск

```bash
# Запустіть worker dyno
heroku ps:scale worker=1

# Перевірте статус
heroku ps

# Перегляньте логи
heroku logs --tail
```

## Крок 6: Перевірка

Якщо все налаштовано правильно, у логах ви побачите:
```
INFO - Підключення до Supabase успішно встановлено
INFO - Бот запущено успішно
```

## 🔧 Додаткові команди

```bash
# Перезапуск бота
heroku restart

# Перегляд змінних середовища
heroku config

# Доступ до bash
heroku run bash

# Моніторинг метрик
heroku logs --tail
```

## 📊 Моніторинг

### Heroku Metrics
- Відкрийте Dashboard → your-app → Metrics
- Перевіряйте використання dyno hours
- Моніторьте помилки та час відповіді

### Supabase Analytics
- Відкрийте Supabase Dashboard
- Перевіряйте кількість запитів
- Моніторьте використання storage

## 🐛 Вирішення проблем

### Бот не запускається
```bash
# Перевірте логи
heroku logs --tail

# Перевірте змінні середовища
heroku config

# Перезапустіть
heroku restart
```

### Помилки бази даних
- Перевірте правильність SUPABASE_URL та SUPABASE_KEY
- Переконайтеся, що таблиці створені в Supabase
- Перевірте інтернет-з'єднання між Heroku та Supabase

### Перевищення лімітів
- **Heroku**: перевірте використання dyno hours в Dashboard
- **Supabase**: перевірте лімити API запитів

## 💡 Поради для продакшену

1. **Використовуйте Heroku Postgres** як додаткову базу для логів
2. **Налаштуйте моніторинг** через Heroku Metrics та Supabase Analytics
3. **Створіть staging середовище** для тестування
4. **Налаштуйте автоматичний деплой** через GitHub
5. **Використовуйте environment branches** для різних стадій розробки

## 💰 Вартість

### Безкоштовні ліміти:
- **Heroku**: 550-1000 dyno hours/місяць
- **Supabase**: 500MB database, 50MB storage, 2GB bandwidth

### Платні плани:
- **Heroku Hobby**: $7/місяць за dyno
- **Supabase Pro**: $25/місяць за проект

## 🔄 Автоматичний деплой

Налаштуйте автоматичний деплой через GitHub:

1. Підключіть репозиторій до Heroku
2. Увімкніть автоматичний деплой з main гілки
3. Увімкніть "Wait for CI to pass"
4. Тепер кожен push в main буде автоматично деплоїтися

```bash
# Створіть GitHub Actions для CI/CD (опціонально)
mkdir -p .github/workflows
# Додайте workflow файл для тестування перед деплоєм
``` 