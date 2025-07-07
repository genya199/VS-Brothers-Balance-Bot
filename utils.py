import re
import logging
from typing import Optional, Tuple
from datetime import datetime
from config import DATE_FORMAT

# Налаштування логування
logger = logging.getLogger(__name__)


def parse_amount_from_text(text: str) -> Optional[float]:
    """
    Парсинг суми з тексту повідомлення
    
    Підтримує різні формати:
    - "= 740 євро"
    - "комплекс 700 євро"
    - "740 euro"
    - "740EUR"
    - "€740"
    
    Args:
        text: Текст для парсингу
        
    Returns:
        Optional[float]: Знайдена сума або None
    """
    # Нормалізуємо текст (прибираємо зайві пробіли, переводимо в нижній регістр для пошуку)
    normalized_text = re.sub(r'\s+', ' ', text.strip())
    
    # Різні патерни для пошуку сум
    patterns = [
        # Формат "= 740 євро"
        r'=\s*(\d+(?:[,.]?\d+)?)\s*(?:євро|euro|eur|€)',
        
        # Формат "комплекс 700 євро"
        r'комплекс\s+(\d+(?:[,.]?\d+)?)\s*(?:євро|euro|eur|€)',
        
        # Формат "до сплати 740 євро"
        r'до\s+сплати\s+(\d+(?:[,.]?\d+)?)\s*(?:євро|euro|eur|€)',
        
        # Формат "сплати 740 євро"
        r'сплати\s+(\d+(?:[,.]?\d+)?)\s*(?:євро|euro|eur|€)',
        
        # Формат "740 євро"
        r'(\d+(?:[,.]?\d+)?)\s*(?:євро|euro|eur|€)',
        
        # Формат "€740"
        r'€\s*(\d+(?:[,.]?\d+)?)',
        
        # Формат "740EUR"
        r'(\d+(?:[,.]?\d+)?)(?:EUR|eur)',
        
        # Загальний формат з числом та валютою
        r'(\d+(?:[,.]?\d+)?)\s*(?:євро|euro|eur|€|\$|usd)',
    ]
    
    # Пробуємо кожен патерн
    for pattern in patterns:
        matches = re.findall(pattern, normalized_text, re.IGNORECASE)
        if matches:
            try:
                # Беремо останню знайдену суму (зазвичай це підсумкова сума)
                amount_str = matches[-1]
                # Замінюємо кому на крапку для правильного парсингу
                amount_str = amount_str.replace(',', '.')
                amount = float(amount_str)
                
                if amount > 0:
                    logger.info(f"Знайдено суму: {amount} у тексті: {text[:50]}...")
                    return amount
                    
            except ValueError:
                continue
    
    logger.warning(f"Не вдалося знайти суму у тексті: {text[:50]}...")
    return None


def extract_car_info(text: str) -> str:
    """
    Витягування інформації про автомобіль з тексту
    
    Args:
        text: Текст для аналізу
        
    Returns:
        str: Інформація про автомобіль
    """
    # Патерни для пошуку інформації про авто
    car_patterns = [
        # Формат "2018TESLA MODEL S 5YJSA1E22JF272459"
        r'(\d{4}[A-Z\s]+(?:MODEL\s+)?[A-Z0-9\s]+[A-Z0-9]{17})',
        
        # VIN код (17 символів)
        r'([A-HJ-NPR-Z0-9]{17})',
        
        # Рік + марка + модель
        r'(\d{4}\s*[A-Z][A-Za-z]+\s+[A-Za-z0-9\s]+)',
        
        # Марка + модель
        r'([A-Z][A-Za-z]+\s+[A-Za-z0-9\s]+(?:MODEL|model)[A-Za-z0-9\s]*)',
    ]
    
    for pattern in car_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            car_info = match.group(1).strip()
            # Очищуємо від зайвих символів
            car_info = re.sub(r'\s+', ' ', car_info)
            logger.info(f"Знайдено інформацію про авто: {car_info}")
            return car_info
    
    # Якщо нічого не знайдено, повертаємо перші слова тексту
    words = text.split()[:5]
    fallback_info = ' '.join(words)
    logger.info(f"Використовуємо fallback інформацію про авто: {fallback_info}")
    return fallback_info


def validate_amount(amount_str: str) -> Tuple[bool, Optional[float]]:
    """
    Валідація введеної користувачем суми
    
    Args:
        amount_str: Рядок з сумою
        
    Returns:
        Tuple[bool, Optional[float]]: (валідна, сума)
    """
    try:
        # Видаляємо пробіли та замінюємо кому на крапку
        clean_amount = amount_str.strip().replace(',', '.')
        
        # Видаляємо символи валют якщо є
        clean_amount = re.sub(r'[€$]', '', clean_amount)
        
        amount = float(clean_amount)
        
        if amount <= 0:
            logger.warning(f"Некоректна сума: {amount} (повинна бути більше 0)")
            return False, None
        
        if amount > 1000000:  # Максимум 1 мільйон
            logger.warning(f"Сума занадто велика: {amount}")
            return False, None
            
        return True, amount
        
    except ValueError:
        logger.warning(f"Некоректний формат суми: {amount_str}")
        return False, None


def format_currency(amount: float) -> str:
    """
    Форматування суми у валюті
    
    Args:
        amount: Сума
        
    Returns:
        str: Форматована сума
    """
    return f"{amount:.2f} €"


def format_balance(balance: float) -> str:
    """
    Форматування балансу з кольоровими індикаторами
    
    Args:
        balance: Баланс
        
    Returns:
        str: Форматований баланс з кольоровими індикаторами
    """
    if balance > 0:
        return f"🟢 ➕ **+{balance:.2f} €** (переплата)"
    elif balance < 0:
        return f"🔴 ➖ **{balance:.2f} €** (борг)"
    else:
        return f"⚖️ ⚪ **{balance:.2f} €** (збалансовано)"


def format_date(date_str: str) -> str:
    """
    Форматування дати у зручний вигляд
    
    Args:
        date_str: Дата у форматі YYYY-MM-DD, DD.MM.YYYY або ISO
        
    Returns:
        str: Форматована дата
    """
    try:
        # Обробляємо ISO формат з часом (2025-07-07T23:21:45.634288+00:00)
        if 'T' in date_str:
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        elif '-' in date_str:
            # Формат YYYY-MM-DD
            date_obj = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
        else:
            # Формат DD.MM.YYYY
            date_obj = datetime.strptime(date_str, DATE_FORMAT)
        
        return date_obj.strftime(DATE_FORMAT)
        
    except ValueError:
        # Якщо не вдалося розпарсити, повертаємо як є
        return date_str


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Обрізання тексту до заданої довжини
    
    Args:
        text: Текст для обрізання
        max_length: Максимальна довжина
        
    Returns:
        str: Обрізаний текст
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def sanitize_filename(filename: str) -> str:
    """
    Очищення назви файлу від недопустимих символів
    
    Args:
        filename: Назва файлу
        
    Returns:
        str: Очищена назва файлу
    """
    # Замінюємо недопустимі символи на підкреслення
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Прибираємо зайві пробіли
    sanitized = re.sub(r'\s+', '_', sanitized.strip())
    
    return sanitized


def parse_date_from_callback(callback_data: str) -> Optional[str]:
    """
    Парсинг дати з callback_data календаря
    
    Args:
        callback_data: Дані з кнопки календаря
        
    Returns:
        Optional[str]: Дата у форматі DD.MM.YYYY або None
    """
    try:
        # Формат: date_selected_YYYY_MM_DD
        parts = callback_data.split('_')
        if len(parts) >= 4:
            year = int(parts[2])
            month = int(parts[3])
            day = int(parts[4])
            
            date_obj = datetime(year, month, day)
            return date_obj.strftime(DATE_FORMAT)
            
    except (ValueError, IndexError):
        logger.error(f"Помилка парсингу дати з callback: {callback_data}")
        
    return None


def is_valid_date(date_str: str) -> bool:
    """
    Перевірка валідності дати
    
    Args:
        date_str: Рядок з датою
        
    Returns:
        bool: True якщо дата валідна
    """
    try:
        datetime.strptime(date_str, DATE_FORMAT)
        return True
    except ValueError:
        return False


def get_operation_emoji(operation_type: str) -> str:
    """
    Отримання емодзі для типу операції
    
    Args:
        operation_type: Тип операції (invoice/payment)
        
    Returns:
        str: Емодзі
    """
    return "📄" if operation_type == "invoice" else "💳"


def extract_car_model_and_vin(car_info: str) -> tuple:
    """
    Виділення моделі авто та VIN коду з рядка
    
    Args:
        car_info: Інформація про авто
        
    Returns:
        tuple: (модель, VIN)
    """
    if not car_info:
        return "Невідоме авто", ""
    
    # Шукаємо VIN (зазвичай 17 символів в кінці)
    parts = car_info.split()
    vin = ""
    model = car_info
    
    for part in parts:
        if len(part) == 17 and part.isalnum():  # VIN код точно 17 символів
            vin = part
            model = car_info.replace(part, '').strip()
            break
    
    return model.strip() if model.strip() else "Невідоме авто", vin


def calculate_balance_for_operations(operations: list) -> dict:
    """
    Розраховує баланс після кожної операції
    
    Args:
        operations: Список операцій
        
    Returns:
        dict: Словник {operation_id: balance_after_operation}
    """
    # Сортуємо операції за датою створення (від старіших до новіших)
    sorted_ops = sorted(operations, key=lambda x: x.get('date', ''), reverse=False)
    
    balance = 0.0
    balance_history = {}
    
    for operation in sorted_ops:
        # Додаємо або віднімаємо суму операції
        amount = float(operation.get('amount', 0))
        balance += amount
        
        # Зберігаємо баланс для цієї операції
        operation_id = f"{operation.get('type', '')}_{operation.get('id', '')}"
        balance_history[operation_id] = balance
    
    return balance_history


def format_operation_summary(operation, balance=None):
    """Форматує підсумок операції для відображення в історії"""
    try:
        operation_type = operation['type']
        amount = float(operation['amount'])
        date_str = format_date(operation.get('date', ''))
        
        if operation_type == 'payment':
            # Платіж - структурований формат
            payment_type = operation.get('payment_type', 'balance')
            operation_id = operation.get('id', '')
            
            # Перша строка: номер та сума
            result = f"🟢 ПЛАТІЖ #{operation_id} +{amount:.2f}€\n"
            
            # Друга строка: за що було поповнення
            if payment_type == 'invoice':
                car_info = operation.get('car_info', 'Невідоме авто')
                car_model, vin = extract_car_model_and_vin(car_info)
                if vin:
                    result += f"🎯 За рахунок: {car_model} | VIN: {vin}\n"
                else:
                    result += f"🎯 За рахунок: {car_model}\n"
            else:
                result += f"🎯 На баланс\n"
            
            # Третя строка: дата
            result += f"📅 {date_str}"
            
            return result
                
        else:  # invoice
            # Рахунок - структурований формат
            car_info = operation.get('car_info', '')
            car_model, vin = extract_car_model_and_vin(car_info)
            operation_id = operation.get('id', '')
            
            # Перша строка: номер рахунку та сума
            result = f"🔴 РАХУНОК #{operation_id} -{abs(amount):.2f}€\n"
            
            # Друга строка: модель та VIN
            result += f"🚗 {car_model} | VIN: {vin}\n"
            
            # Третя строка: дата
            result += f"📅 {date_str}"
            
            return result
        
    except Exception as e:
        logger.error(f"Помилка форматування операції: {e}")
        return f"❌ Помилка відображення операції: {operation.get('id', 'невідомо')}"


def format_single_operation_summary(operation):
    """Форматує одну операцію для показу в списках видалення"""
    if operation['type'] == 'payment':
        # Поповнення
        text = f"🟢 ПОПОВНЕННЯ +{operation['amount']:.2f}€\n"
        if operation.get('payment_type') == 'balance':
            text += f"🗓️ {format_date(operation['date'])} • На баланс"
        else:
            # Платіж за рахунок
            car_model, vin = extract_car_model_and_vin(operation.get('car_info', ''))
            text += f"🗓️ {format_date(operation['date'])} • За: {car_model}"
    else:
        # Рахунок
        car_model, vin = extract_car_model_and_vin(operation.get('car_info', ''))
        text = f"🔴 РАХУНОК {abs(operation['amount']):.2f}€\n"  # Используем abs() для отрицательных сумм
        text += f"🚗 {car_model}\n"
        text += f"🆔 VIN: {vin}\n"
        text += f"🗓️ {format_date(operation['date'])}"
    
    return text 