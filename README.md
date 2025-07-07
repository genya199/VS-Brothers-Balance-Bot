# 🚗 VS Brothers Balance Bot

Telegram бот для управління фінансовими операціями автосервісу VS Brothers. Автоматично обробляє рахунки, платежі та веде облік балансу клієнтів.

![Bot Demo](https://img.shields.io/badge/Telegram-Bot-blue?logo=telegram)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Database](https://img.shields.io/badge/Database-Supabase-green)

## ✨ Основні функції

### 📋 Управління рахунками
- **Автоматичне розпізнавання** рахунків з повідомлень
- **Інтелектуальний парсинг** сум з пріоритизацією (= євро > комплекс > до сплати)
- **Витягування інформації** про автомобіль та VIN-код
- **Гнучкі формати** підтримки рахунків

### 💰 Система платежів
- **Два типи платежів**: на конкретний рахунок або на загальний баланс
- **Автоматичне оновлення** балансу
- **Підтримка різних валют** (євро за замовчуванням)
- **Історія операцій** з детальною інформацією

### 📊 Звітність та аналітика
- **Кольорове відображення** операцій (🟢 доходи / 🔴 витрати)
- **Структурована історія** з VIN-кодами та датами
- **Експорт в TXT** з хронологічним порядком та підрахунком балансу
- **Поточний баланс** з кольоровими індикаторами

### 🗑️ Управління операціями
- **Видалення операцій** з інтуїтивними кнопками
- **Автоматичне оновлення** балансу при видаленні
- **Безпечне підтвердження** операцій

## 🔧 Технології

- **Backend**: Python 3.9+, aiogram 2.x
- **База даних**: Supabase (PostgreSQL)
- **Деплой**: Heroku
- **API**: Telegram Bot API

## 📱 Формати рахунків

Бот підтримує різні формати повідомлень з рахунками:

```
🚗 2018TESLA MODEL S 5YJSA1E22JF272459
💰 Діагностика = 150 євро
🔧 Ремонт підвіски = 698 євро
⚙️ Всього до сплати = 848 євро
```

Детальну інформацію про підтримувані формати див. в [SUPPORTED_FORMATS.md](SUPPORTED_FORMATS.md)

## 🏗️ Архітектура

```
vs-brothers-bot/
├── main.py              # Основна логіка бота
├── utils.py             # Допоміжні функції
├── keyboards.py         # Telegram клавіатури
├── supabase_database.py # Робота з базою даних
├── config.py           # Конфігурація
├── requirements.txt    # Залежності
├── Procfile           # Heroku конфігурація
└── docs/              # Документація
```

## 🚀 Швидкий старт

### 1. Клонування репозиторію
```bash
git clone https://github.com/yourusername/vs-brothers-bot.git
cd vs-brothers-bot
```

### 2. Налаштування середовища
```bash
cp .env.example .env
# Відредагуйте .env файл з вашими налаштуваннями
```

### 3. Встановлення залежностей
```bash
pip install -r requirements.txt
```

### 4. Запуск
```bash
python main.py
```

## ⚙️ Конфігурація

Створіть файл `.env` на основі `.env.example`:

```env
# Telegram Bot Token (отримайте у @BotFather)
BOT_TOKEN=your_bot_token_here

# Supabase конфігурація
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key

# ID адміністратора бота
ADMIN_USER_ID=your_telegram_user_id
```

## 🛠️ Налаштування бази даних

Детальні інструкції з налаштування Supabase див. в [SETUP_GUIDE.md](SETUP_GUIDE.md)

## 🚀 Деплой на Heroku

Повні інструкції з деплою див. в [HEROKU_DEPLOY.md](HEROKU_DEPLOY.md)

```bash
heroku create your-bot-name
heroku config:set BOT_TOKEN=your_token
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_KEY=your_key
git push heroku main
```

## 📖 Документація

- [QUICKSTART.md](QUICKSTART.md) - Швидкий старт
- [SETUP_GUIDE.md](SETUP_GUIDE.md) - Повне налаштування
- [ARCHITECTURE.md](ARCHITECTURE.md) - Архітектура системи
- [SUPPORTED_FORMATS.md](SUPPORTED_FORMATS.md) - Формати рахунків
- [HEROKU_DEPLOY.md](HEROKU_DEPLOY.md) - Деплой на Heroku

## 🎯 Приклади використання

### Додавання рахунку
Просто перешліть повідомлення з рахунком боту:
```
2018TESLA MODEL S 5YJSA1E22JF272459
Ремонт = 850 євро
```

### Додавання платежу
Використовуйте команду `/payment` або кнопку "💰 Додати платіж"

### Перегляд історії
```
📋 ІСТОРІЯ ОПЕРАЦІЙ

🔴 РАХУНОК #15 -850.00€
🚗 2018TESLA MODEL S | VIN: 5YJSA1E22JF272459
📅 08.07.2025

🟢 ПЛАТІЖ #16 +500.00€
🎯 За рахунок: 2018TESLA MODEL S | VIN: 5YJSA1E22JF272459
📅 08.07.2025

💰 ПІДСУМОК: 🔴 -350.00€
```

## 🤝 Внесок у проєкт

1. Fork репозиторію
2. Створіть feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit зміни (`git commit -m 'Add AmazingFeature'`)
4. Push в branch (`git push origin feature/AmazingFeature`)
5. Відкрийте Pull Request

## 📄 Ліцензія

Цей проєкт ліцензований під MIT License - див. файл [LICENSE](LICENSE) для деталей.

## 🛡️ Безпека

- Всі конфіденційні дані зберігаються в змінних середовища
- База даних захищена через Supabase RLS (Row Level Security)
- Валідація всіх користувацьких вводів
- Логування операцій для аудиту

## 📞 Підтримка

Якщо у вас виникли питання або проблеми:

1. Перевірте [документацію](docs/)
2. Створіть [Issue](https://github.com/yourusername/vs-brothers-bot/issues)
3. Напишіть розробнику

---

**VS Brothers Balance Bot** - надійне рішення для автоматизації фінансового обліку автосервісу! 🚗💰 
