from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from datetime import datetime, timedelta
import calendar
from config import MAIN_MENU_BUTTONS, MONTHS_UA, WEEKDAYS_UA


def get_main_menu() -> InlineKeyboardMarkup:
    """
    Створення головного меню бота
    
    Returns:
        InlineKeyboardMarkup: Клавіатура головного меню
    """
    builder = InlineKeyboardBuilder()
    
    # Додаємо кнопки у два ряди
    builder.add(
        InlineKeyboardButton(
            text=MAIN_MENU_BUTTONS['new_invoice'],
            callback_data="menu_add_invoice"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=MAIN_MENU_BUTTONS['payment'],
            callback_data="menu_add_payment"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=MAIN_MENU_BUTTONS['balance'],
            callback_data="menu_balance"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=MAIN_MENU_BUTTONS['history'],
            callback_data="menu_history"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text=MAIN_MENU_BUTTONS['export'],
            callback_data="menu_export"
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🗑️ Видалити операції",
            callback_data="delete_operations_menu"
        )
    )
    
    # Розташовуємо кнопки: 2-2-2
    builder.adjust(2, 2, 2)
    
    return builder.as_markup()


def get_back_to_menu() -> InlineKeyboardMarkup:
    """
    Створення клавіатури для повернення в головне меню
    
    Returns:
        InlineKeyboardMarkup: Клавіатура з кнопкою "Назад"
    """
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🏠 Головне меню",
            callback_data="back_to_menu"
        )
    )
    return builder.as_markup()


def get_calendar(year: int = None, month: int = None) -> InlineKeyboardMarkup:
    """
    Створення інлайн календаря для вибору дати
    
    Args:
        year: Рік (за замовчуванням поточний)
        month: Місяць (за замовчуванням поточний)
        
    Returns:
        InlineKeyboardMarkup: Календар
    """
    now = datetime.now()
    if year is None:
        year = now.year
    if month is None:
        month = now.month
    
    builder = InlineKeyboardBuilder()
    
    # Заголовок з місяцем та роком
    builder.add(
        InlineKeyboardButton(
            text=f"{MONTHS_UA[month-1]} {year}",
            callback_data="ignore"
        )
    )
    builder.adjust(1)
    
    # Кнопки навігації
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    
    next_month = month + 1
    next_year = year
    if next_month == 13:
        next_month = 1
        next_year += 1
    
    builder.add(
        InlineKeyboardButton(
            text="⬅️",
            callback_data=f"calendar_prev_{prev_year}_{prev_month}"
        ),
        InlineKeyboardButton(
            text="➡️",
            callback_data=f"calendar_next_{next_year}_{next_month}"
        )
    )
    builder.adjust(2)
    
    # Дні тижня
    for day in WEEKDAYS_UA:
        builder.add(
            InlineKeyboardButton(
                text=day,
                callback_data="ignore"
            )
        )
    builder.adjust(7)
    
    # Дні місяця
    cal = calendar.monthcalendar(year, month)
    
    for week in cal:
        week_buttons = []
        for day in week:
            if day == 0:
                # Порожній день
                week_buttons.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data="ignore"
                    )
                )
            else:
                # Перевіряємо, чи це сьогоднішній день
                is_today = (day == now.day and month == now.month and year == now.year)
                day_text = f"[{day}]" if is_today else str(day)
                
                week_buttons.append(
                    InlineKeyboardButton(
                        text=day_text,
                        callback_data=f"date_selected_{year}_{month:02d}_{day:02d}"
                    )
                )
        
        builder.row(*week_buttons)
    
    # Кнопка "Сьогодні"
    today_date = now.strftime("%Y_%m_%d")
    builder.add(
        InlineKeyboardButton(
            text="📅 Сьогодні",
            callback_data=f"date_selected_{today_date}"
        )
    )
    builder.adjust(1)
    
    # Кнопка "Назад"
    builder.add(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(1)
    
    return builder.as_markup()


def get_confirm_keyboard(action: str, data: str = "") -> InlineKeyboardMarkup:
    """
    Створення клавіатури підтвердження дії
    
    Args:
        action: Тип дії для підтвердження
        data: Додаткові дані
        
    Returns:
        InlineKeyboardMarkup: Клавіатура підтвердження
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="✅ Так",
            callback_data=f"confirm_{action}_{data}"
        ),
        InlineKeyboardButton(
            text="❌ Ні",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(2)
    
    return builder.as_markup()


def get_invoice_selection_keyboard(invoices: list) -> InlineKeyboardMarkup:
    """
    Створення клавіатури для вибору рахунку для оплати
    
    Args:
        invoices: Список рахунків для відображення
        
    Returns:
        InlineKeyboardMarkup: Клавіатура з рахунками
    """
    builder = InlineKeyboardBuilder()
    
    if not invoices:
        # Якщо рахунків немає
        builder.add(
            InlineKeyboardButton(
                text="🚫 Немає рахунків",
                callback_data="ignore"
            )
        )
    else:
        # Додаємо кнопки для кожного рахунку
        for invoice in invoices[:10]:  # Показуємо максимум 10 рахунків
            builder.add(
                InlineKeyboardButton(
                    text=f"📄 {invoice['display_text']}",
                    callback_data=f"select_invoice_{invoice['id']}"
                )
            )
    
    # Додаємо кнопку "На баланс" 
    builder.add(
        InlineKeyboardButton(
            text="💰 Платіж на баланс",
            callback_data="select_invoice_balance"
        )
    )
    
    # Кнопка назад
    builder.add(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_menu"
        )
    )
    
    # Розташовуємо кнопки вертикально
    builder.adjust(1)
    
    return builder.as_markup()


def get_operations_keyboard() -> InlineKeyboardMarkup:
    """
    Створення клавіатури для роботи з операціями
    
    Returns:
        InlineKeyboardMarkup: Клавіатура з операціями
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="🏠 Головне меню",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(1)
    
    return builder.as_markup()


def get_history_keyboard() -> InlineKeyboardMarkup:
    """
    Створення клавіатури для історії операцій
    
    Returns:
        InlineKeyboardMarkup: Клавіатура для історії
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📤 Експорт",
            callback_data="menu_export"
        )
    )
    builder.adjust(1)
    
    builder.add(
        InlineKeyboardButton(
            text="🏠 Головне меню",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(1)
    
    return builder.as_markup()


def get_amount_confirmation_keyboard(amount: float) -> InlineKeyboardMarkup:
    """
    Створення клавіатури для підтвердження суми
    
    Args:
        amount: Сума для підтвердження
        
    Returns:
        InlineKeyboardMarkup: Клавіатура підтвердження суми
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text=f"✅ Підтвердити {amount:.2f} євро",
            callback_data=f"confirm_amount_{amount}"
        )
    )
    builder.adjust(1)
    
    builder.add(
        InlineKeyboardButton(
            text="✏️ Змінити суму",
            callback_data="change_amount"
        ),
        InlineKeyboardButton(
            text="❌ Скасувати",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(2)
    
    return builder.as_markup()


def get_export_keyboard() -> InlineKeyboardMarkup:
    """
    Створення клавіатури для експорту даних
    
    Returns:
        InlineKeyboardMarkup: Клавіатура експорту
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="📋 Текстовий файл",
            callback_data="export_text"
        )
    )
    builder.adjust(1)
    
    builder.add(
        InlineKeyboardButton(
            text="🏠 Головне меню",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(1)
    
    return builder.as_markup()





def get_operations_list_keyboard(operations: list, page: int, total_pages: int) -> InlineKeyboardMarkup:
    """
    Створення клавіатури зі списком операцій для видалення
    
    Args:
        operations: Список операцій
        page: Поточна сторінка
        total_pages: Загальна кількість сторінок
        
    Returns:
        InlineKeyboardMarkup: Клавіатура зі списком операцій
    """
    builder = InlineKeyboardBuilder()
    
    # Додаємо кнопки операцій
    for operation in operations:
        if operation['type'] == 'invoice':
            from utils import extract_car_model_and_vin, format_date
            
            car_info = operation.get('car_info', 'Невідоме авто')
            model, vin = extract_car_model_and_vin(car_info)
            date = format_date(operation.get('date', ''))
            
            # Кольоровий формат: червоний індикатор для рахунків
            if model and model != 'Невідоме авто':
                # Виділяємо тільки марку та модель (без року)
                clean_model = model.replace('2017', '').replace('2018', '').replace('2019', '').replace('2020', '').replace('2021', '').replace('2022', '').replace('2023', '').replace('2024', '').replace('2025', '').strip()
                model_short = clean_model[:12]  # Коротше для VIN та дати
                
                if vin:
                    vin_short = vin[-6:]  # Останні 6 символів VIN
                    text = f"🔴 -{operation['amount']:.0f}€ | {model_short} | ...{vin_short} | {date}"
                else:
                    text = f"🔴 -{operation['amount']:.0f}€ | {model_short} | {date}"
            else:
                text = f"🔴 -{operation['amount']:.0f}€ | Невідоме авто | {date}"
        else:
            from utils import extract_car_model_and_vin, format_date
            
            date = format_date(operation.get('date', ''))
            
            # Визначаємо тип платежу
            if operation.get('invoice_id') and operation.get('invoice_car_info'):
                # Платіж за конкретний рахунок
                car_info = operation['invoice_car_info']
                model, vin = extract_car_model_and_vin(car_info)
                
                if model and model != 'Невідоме авто':
                    # Виділяємо тільки марку та модель
                    clean_model = model.replace('2017', '').replace('2018', '').replace('2019', '').replace('2020', '').replace('2021', '').replace('2022', '').replace('2023', '').replace('2024', '').replace('2025', '').strip()
                    model_short = clean_model[:10]  # Ще коротше для платежів
                    
                    if vin:
                        vin_short = vin[-4:]  # Останні 4 символи для економії місця
                        text = f"🟢 +{operation['amount']:.0f}€ | {model_short} | ...{vin_short} | {date}"
                    else:
                        text = f"🟢 +{operation['amount']:.0f}€ | За {model_short} | {date}"
                else:
                    text = f"🟢 +{operation['amount']:.0f}€ | За рахунок | {date}"
            else:
                # Платіж на баланс
                text = f"🟢 +{operation['amount']:.0f}€ | На баланс | {date}"
        
        builder.add(
            InlineKeyboardButton(
                text=text,
                callback_data=f"delete_{operation['type']}_{operation['id']}"
            )
        )
    
    builder.adjust(1)
    
    # Кнопки навігації
    nav_buttons = []
    
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Попередня",
                callback_data=f"delete_page_{page - 1}"
            )
        )
    
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️ Наступна",
                callback_data=f"delete_page_{page + 1}"
            )
        )
    
    if nav_buttons:
        builder.row(*nav_buttons)
    
    # Показуємо поточну сторінку
    if total_pages > 1:
        builder.add(
            InlineKeyboardButton(
                text=f"📄 {page}/{total_pages}",
                callback_data="ignore"
            )
        )
        builder.adjust(1)
    
    # Кнопка назад
    builder.add(
        InlineKeyboardButton(
            text="🔙 Головне меню",
            callback_data="back_to_menu"
        )
    )
    builder.adjust(1)
    
    return builder.as_markup()


def get_delete_confirmation_keyboard(operation_type: str, operation_id: int) -> InlineKeyboardMarkup:
    """
    Створення клавіатури підтвердження видалення операції
    
    Args:
        operation_type: Тип операції ('invoice' або 'payment')
        operation_id: ID операції
        
    Returns:
        InlineKeyboardMarkup: Клавіатура підтвердження
    """
    builder = InlineKeyboardBuilder()
    
    builder.add(
        InlineKeyboardButton(
            text="🗑️ Так, видалити",
            callback_data=f"confirm_delete_{operation_type}_{operation_id}"
        ),
        InlineKeyboardButton(
            text="❌ Скасувати",
            callback_data="delete_operations_menu"
        )
    )
    builder.adjust(2)
    
    return builder.as_markup() 