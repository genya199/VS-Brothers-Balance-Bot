import asyncio
import logging
import sqlite3
import sys
from datetime import datetime
from io import StringIO

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.exceptions import TelegramBadRequest

# Імпорти наших модулів
from config import BOT_TOKEN, MESSAGES
from supabase_database import initialize_database
from keyboards import (
    get_main_menu, get_back_to_menu, get_calendar, 
    get_history_keyboard, get_operations_keyboard,
    get_amount_confirmation_keyboard, get_export_keyboard,
    get_operations_list_keyboard, get_delete_confirmation_keyboard, 
    get_invoice_selection_keyboard
)
from utils import (
    parse_amount_from_text, extract_car_info, validate_amount,
    format_balance, format_date, parse_date_from_callback,
    format_operation_summary, format_single_operation_summary, 
    sanitize_filename
)

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Створення бота та диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Глобальна змінна для бази даних
db = None


# Стани для FSM (Finite State Machine)
class BotStates(StatesGroup):
    waiting_for_invoice_text = State()
    waiting_for_payment_amount = State()
    waiting_for_payment_date = State()
    waiting_for_payment_invoice_selection = State()
    deleting_operations = State()


# Хендлер команди /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обробка команди /start"""
    try:
        await message.answer(
            MESSAGES['start'],
            reply_markup=get_main_menu()
        )
        logger.info(f"Користувач {message.from_user.id} запустив бота")
    except Exception as e:
        logger.error(f"Помилка в cmd_start: {e}")
        await message.answer(MESSAGES['error'])


# Хендлер для повернення в головне меню
@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Повернення в головне меню"""
    try:
        await state.clear()
        await callback.message.edit_text(
            MESSAGES['start'],
            reply_markup=get_main_menu()
        )
        await callback.answer()
    except TelegramBadRequest:
        # Якщо повідомлення не можна редагувати, відправляємо нове
        await callback.message.answer(
            MESSAGES['start'],
            reply_markup=get_main_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка в back_to_menu: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для додавання рахунку
@dp.callback_query(F.data == "menu_add_invoice")
async def add_invoice_start(callback: CallbackQuery, state: FSMContext):
    """Початок додавання рахунку"""
    try:
        await state.set_state(BotStates.waiting_for_invoice_text)
        await callback.message.edit_text(
            MESSAGES['add_invoice'],
            reply_markup=get_back_to_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка в add_invoice_start: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для обробки тексту рахунку
@dp.message(StateFilter(BotStates.waiting_for_invoice_text))
async def process_invoice_text(message: Message, state: FSMContext):
    """Обробка тексту повідомлення з рахунком"""
    try:
        text = message.text
        
        # Парсимо суму з тексту
        amount = parse_amount_from_text(text)
        
        if amount is None:
            await message.answer(
                MESSAGES['no_amount_found'],
                reply_markup=get_back_to_menu()
            )
            return
        
        # Витягуємо інформацію про авто
        car_info = extract_car_info(text)
        
        # Додаємо рахунок в базу даних
        success = db.add_invoice(
            user_id=message.from_user.id,
            car_info=car_info,
            amount=amount,
            original_text=text
        )
        
        if success:
            await state.clear()
            balance = db.get_balance(message.from_user.id)
            
            response = f"{MESSAGES['invoice_added']}\n\n"
            response += f"🚗 Авто: {car_info}\n"
            response += f"💰 Сума: {amount:.2f} €\n\n"
            response += f"📊 Поточний баланс:\n{format_balance(balance)}"
            
            await message.answer(
                response,
                reply_markup=get_main_menu()
            )
        else:
            await message.answer(
                MESSAGES['error'],
                reply_markup=get_main_menu()
            )
            
    except Exception as e:
        logger.error(f"Помилка в process_invoice_text: {e}")
        await message.answer(
            MESSAGES['error'],
            reply_markup=get_main_menu()
        )
        await state.clear()


# Хендлер для додавання платежу
@dp.callback_query(F.data == "menu_add_payment")
async def add_payment_start(callback: CallbackQuery, state: FSMContext):
    """Початок додавання платежу - введення суми"""
    try:
        await state.set_state(BotStates.waiting_for_payment_amount)
        await callback.message.edit_text(
            MESSAGES['add_payment'],
            reply_markup=get_back_to_menu()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка в add_payment_start: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для обробки суми платежу
@dp.message(StateFilter(BotStates.waiting_for_payment_amount))
async def process_payment_amount(message: Message, state: FSMContext):
    """Обробка суми платежу - показуємо календар"""
    try:
        is_valid, amount = validate_amount(message.text)
        
        if not is_valid:
            await message.answer(
                MESSAGES['invalid_amount'],
                reply_markup=get_back_to_menu()
            )
            return
        
        # Зберігаємо суму в стан
        await state.update_data(payment_amount=amount)
        await state.set_state(BotStates.waiting_for_payment_date)
        
        await message.answer(
            f"✅ Сума: {amount:.2f} €\n\n📅 Оберіть дату платежу:",
            reply_markup=get_calendar()
        )
        
    except Exception as e:
        logger.error(f"Помилка в process_payment_amount: {e}")
        await message.answer(
            MESSAGES['error'],
            reply_markup=get_main_menu()
        )
        await state.clear()


# Хендлер для навігації календаря
@dp.callback_query(F.data.startswith("calendar_"))
async def calendar_navigation(callback: CallbackQuery):
    """Навігація по календарю"""
    try:
        data = callback.data
        
        if data.startswith("calendar_prev_"):
            # Попередній місяць
            _, _, year, month = data.split('_')
            await callback.message.edit_reply_markup(
                reply_markup=get_calendar(int(year), int(month))
            )
        elif data.startswith("calendar_next_"):
            # Наступний місяць
            _, _, year, month = data.split('_')
            await callback.message.edit_reply_markup(
                reply_markup=get_calendar(int(year), int(month))
            )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в calendar_navigation: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для вибору дати
@dp.callback_query(F.data.startswith("date_selected_"))
async def date_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору дати платежу - показуємо 5 останніх рахунків"""
    try:
        # Парсимо дату з callback_data
        selected_date = parse_date_from_callback(callback.data)
        
        if not selected_date:
            await callback.answer("Помилка вибору дати")
            return
        
        # Отримуємо дані зі стану
        state_data = await state.get_data()
        payment_amount = state_data.get('payment_amount')
        
        if not payment_amount:
            await callback.answer("Помилка: втрачено суму платежу")
            await state.clear()
            return
        
        # Отримуємо останні 5 рахунків користувача
        recent_invoices = db.get_recent_invoices(callback.from_user.id, limit=5)
        
        response = f"💰 Сума: {payment_amount:.2f} €\n📅 Дата: {selected_date}\n\n"
        if recent_invoices:
            response += "📄 Оберіть рахунок для оплати або натисніть 'На баланс':\n\n"
            response += "🕐 Останні 5 рахунків:"
        else:
            response += "📭 У вас немає рахунків.\nМожете зробити платіж на баланс:"
        
        # Зберігаємо дату і суму для фінального кроку
        await state.update_data(payment_date=selected_date, final_amount=payment_amount)
        await state.set_state(BotStates.waiting_for_payment_invoice_selection)
        
        await callback.message.edit_text(
            response,
            reply_markup=get_invoice_selection_keyboard(recent_invoices)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в date_selected: {e}")
        await callback.answer("Сталася помилка")
        await state.clear()


# Хендлер для вибору рахунку або "на баланс"
@dp.callback_query(F.data.startswith("select_invoice_"))
async def invoice_selected(callback: CallbackQuery, state: FSMContext):
    """Обробка вибору рахунку для оплати - відразу створюємо платіж"""
    try:
        # Отримуємо дані зі стану
        state_data = await state.get_data()
        payment_date = state_data.get('payment_date')
        final_amount = state_data.get('final_amount')
        
        if not payment_date or not final_amount:
            await callback.answer("Помилка: втрачено дані платежу")
            await state.clear()
            return
        
        # Парсимо ID рахунку з callback_data
        callback_parts = callback.data.split('_')
        
        if callback_parts[2] == "balance":
            # Платіж на баланс
            success = db.add_payment(
                user_id=callback.from_user.id,
                amount=final_amount,
                date_paid=payment_date
            )
            payment_description = "на баланс"
        else:
            # Платіж за конкретний рахунок
            invoice_id = int(callback_parts[2])
            
            # Отримуємо інформацію про рахунок для перевірки
            recent_invoices = db.get_recent_invoices(callback.from_user.id, limit=5)
            selected_invoice = next((inv for inv in recent_invoices if inv['id'] == invoice_id), None)
            
            if not selected_invoice:
                await callback.answer("Рахунок не знайдено")
                return
            
            success = db.add_payment_for_invoice(
                user_id=callback.from_user.id,
                invoice_id=invoice_id,
                amount=final_amount,
                date_paid=payment_date
            )
            payment_description = f"за рахунок: {selected_invoice['car_info']}"
        
        if success:
            await state.clear()
            balance = db.get_balance(callback.from_user.id)
            
            response = f"✅ Платіж успішно додано!\n\n"
            response += f"💰 Сума: {final_amount:.2f} €\n"
            response += f"📅 Дата: {payment_date}\n"
            response += f"📄 Тип: Платіж {payment_description}\n\n"
            response += f"📊 Поточний баланс:\n{format_balance(balance)}"
            
            await callback.message.edit_text(
                response,
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.edit_text(
                MESSAGES['error'],
                reply_markup=get_main_menu()
            )
            await state.clear()
            
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в invoice_selected: {e}")
        await callback.answer("Сталася помилка")
        await state.clear()





# Хендлер для перегляду балансу
@dp.callback_query(F.data == "menu_balance")
async def show_balance(callback: CallbackQuery):
    """Показ поточного балансу"""
    try:
        balance = db.get_balance(callback.from_user.id)
        
        response = f"{MESSAGES['balance']}\n\n"
        response += format_balance(balance)
        
        await callback.message.edit_text(
            response,
            reply_markup=get_operations_keyboard()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в show_balance: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для перегляду історії
@dp.callback_query(F.data == "menu_history")
async def show_history(callback: CallbackQuery):
    """Показ історії операцій"""
    try:
        user_id = callback.from_user.id
        history = db.get_history(user_id)
        current_balance = db.get_balance(user_id)
        
        # Заголовок згідно зображення
        response = "🏠 VA BROTHERS BALANCE\n\n"
        
        if not history:
            balance_emoji = "⚪" if current_balance == 0 else ("🟢" if current_balance > 0 else "🔴")
            response += f"Немає операцій\n\n💰 ПІДСУМОК: {balance_emoji} {current_balance:.2f} €"
        else:
            # Форматуємо кожну операцію
            for operation in history[:15]:  # Обмежуємо до 15 операцій
                operation_text = format_operation_summary(operation)
                response += operation_text + "\n\n"
            
            # Додаємо підсумок згідно зображення
            balance_emoji = "⚪" if current_balance == 0 else ("🟢" if current_balance > 0 else "🔴")
            if current_balance < 0:
                response += f"💰 ПІДСУМОК: {balance_emoji} {current_balance:.2f} €"
            else:
                response += f"💰 ПІДСУМОК: {balance_emoji} +{current_balance:.2f} €"
        
        # Обмежуємо довжину повідомлення
        if len(response) > 4000:
            response = response[:4000] + "...\n\n💰 ПІДСУМОК: €" + str(current_balance)
        
        await callback.message.edit_text(
            response,
            reply_markup=get_back_to_menu()
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в show_history: {e}")
        await callback.answer("❌ Помилка при отриманні історії")
        await callback.message.answer("❌ Помилка при отриманні історії операцій")




# Хендлер для експорту
@dp.callback_query(F.data == "menu_export")
async def export_menu(callback: CallbackQuery):
    """Меню експорту"""
    try:
        await callback.message.edit_text(
            "📤 Оберіть формат експорту:",
            reply_markup=get_export_keyboard()
        )
        await callback.answer()
    except Exception as e:
        logger.error(f"Помилка в export_menu: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для експорту в текстовий файл
@dp.callback_query(F.data == "export_text")
async def export_text(callback: CallbackQuery):
    """Експорт історії в текстовий файл"""
    try:
        # Отримуємо експорт з бази даних
        export_data = db.export_history(callback.from_user.id)
        
        # Створюємо файл
        filename = f"car_payments_export_{callback.from_user.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        filename = sanitize_filename(filename)
        
        # Записуємо дані у файл
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(export_data)
        
        # Відправляємо файл користувачу
        document = FSInputFile(filename)
        await callback.message.answer_document(
            document,
            caption="📋 Експорт історії операцій"
        )
        
        # Видаляємо тимчасовий файл
        import os
        os.remove(filename)
        
        await callback.message.edit_text(
            "✅ Експорт завершено!",
            reply_markup=get_main_menu()
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в export_text: {e}")
        await callback.answer("Сталася помилка експорту")


# Хендлер для меню видалення операцій
@dp.callback_query(F.data == "delete_operations_menu")
async def delete_operations_menu(callback: CallbackQuery, state: FSMContext):
    """Відображення списку операцій для видалення"""
    try:
        await state.set_state(BotStates.deleting_operations)
        user_id = callback.from_user.id
        operations, total_count, total_pages = db.get_paginated_history(user_id, page=1, per_page=5)
        
        if not operations:
            await callback.message.edit_text(
                "📋 Немає операцій для видалення",
                reply_markup=get_back_to_menu()
            )
            await callback.answer()
            return
        
        await state.update_data(delete_page=1)
        
        text = f"🗑️ Оберіть операцію для видалення:\n\n"
        for i, op in enumerate(operations, 1):
            # Використовуємо функцію для окремих операцій
            summary = format_single_operation_summary(op)
            text += f"{i}. {summary}\n\n"
        
        if total_pages > 1:
            text += f"📄 Сторінка 1/{total_pages}"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_operations_list_keyboard(operations, 1, total_pages)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в delete_operations_menu: {e}")
        await callback.answer("Сталася помилка")




# Хендлер для навігації по сторінках видалення
@dp.callback_query(F.data.startswith("delete_page_"))
async def delete_page_navigation(callback: CallbackQuery, state: FSMContext):
    """Навігація по сторінках для видалення"""
    try:
        page = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id
        
        operations, total_count, total_pages = db.get_paginated_history(user_id, page=page, per_page=5)
        
        if not operations:
            await callback.answer("Немає операцій на цій сторінці")
            return
        
        await state.update_data(delete_page=page)
        
        text = f"🗑️ Оберіть операцію для видалення:\n\n"
        for i, op in enumerate(operations, 1):
            # Використовуємо функцію для окремих операцій
            summary = format_single_operation_summary(op)
            text += f"{i}. {summary}\n\n"
        
        if total_pages > 1:
            text += f"📄 Сторінка {page}/{total_pages}"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_operations_list_keyboard(operations, page, total_pages)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в delete_page_navigation: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для вибору операції для видалення
@dp.callback_query(F.data.startswith("delete_invoice_") | F.data.startswith("delete_payment_"))
async def select_operation_for_deletion(callback: CallbackQuery, state: FSMContext):
    """Підтвердження видалення операції"""
    try:
        parts = callback.data.split("_")
        operation_type = parts[1]  # 'invoice' або 'payment'
        operation_id = int(parts[2])
        user_id = callback.from_user.id
        
        # Отримуємо деталі операції з Supabase
        if operation_type == 'invoice':
            result_data = db.supabase.table('invoices')\
                .select('car_info, amount, date_created, original_text')\
                .eq('id', operation_id)\
                .eq('user_id', user_id)\
                .execute()
        else:  # payment
            result_data = db.supabase.table('payments')\
                .select('amount, date_paid, date_created')\
                .eq('id', operation_id)\
                .eq('user_id', user_id)\
                .execute()
        
        result = result_data.data[0] if result_data.data else None
        
        if not result:
            await callback.answer("Операція не знайдена")
            return
        
        # Формуємо текст підтвердження
        if operation_type == 'invoice':
            text = f"🗑️ Видалити рахунок?\n\n"
            text += f"📄 Тип: Рахунок\n"
            text += f"🚗 Авто: {result['car_info']}\n"
            text += f"💰 Сума: {float(result['amount']):.2f}€\n"
            # Форматуємо дату правильно
            created_date = result['date_created'][:10] if result['date_created'] else 'Невідомо'
            text += f"🕐 Створено: {created_date}\n"
            if result.get('original_text'):
                preview = result['original_text'][:100] + "..." if len(result['original_text']) > 100 else result['original_text']
                text += f"📝 Текст: {preview}\n"
        else:  # payment
            text = f"🗑️ Видалити платіж?\n\n"
            text += f"💳 Тип: Платіж\n"
            text += f"💰 Сума: {float(result['amount']):.2f}€\n"
            text += f"📅 Дата платежу: {result.get('date_paid', 'Невідомо')}\n"
            # Форматуємо дату правильно
            created_date = result['date_created'][:10] if result['date_created'] else 'Невідомо'
            text += f"🕐 Створено: {created_date}\n"
        
        text += f"\n⚠️ Ця дія незворотна!"
        
        await callback.message.edit_text(
            text,
            reply_markup=get_delete_confirmation_keyboard(operation_type, operation_id)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в select_operation_for_deletion: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для підтвердження видалення операції
@dp.callback_query(F.data.startswith("confirm_delete_"))
async def confirm_delete_operation(callback: CallbackQuery, state: FSMContext):
    """Виконання видалення операції"""
    try:
        parts = callback.data.split("_")
        operation_type = parts[2]  # 'invoice' або 'payment'
        operation_id = int(parts[3])
        user_id = callback.from_user.id
        
        # Видаляємо операцію
        if operation_type == 'invoice':
            success = db.delete_invoice_by_id(user_id, operation_id)
            op_name = "рахунок"
        else:  # payment
            success = db.delete_payment_by_id(user_id, operation_id)
            op_name = "платіж"
        
        if success:
            balance = db.get_balance(user_id)
            
            text = f"✅ {op_name.capitalize()} успішно видалено!\n\n"
            text += f"📊 Поточний баланс:\n{format_balance(balance)}"
            
            await callback.message.edit_text(
                text,
                reply_markup=get_main_menu()
            )
        else:
            await callback.message.edit_text(
                f"❌ Не вдалося видалити {op_name}",
                reply_markup=get_main_menu()
            )
        
        await state.clear()
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Помилка в confirm_delete_operation: {e}")
        await callback.answer("Сталася помилка")


# Хендлер для ігнорування callback'ів
@dp.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    """Ігнорування натискання на неактивні кнопки"""
    await callback.answer()


# Хендлер для обробки невідомих повідомлень
@dp.message()
async def unknown_message(message: Message, state: FSMContext):
    """Обробка невідомих повідомлень"""
    current_state = await state.get_state()
    
    # Якщо бот очікує введення тексту рахунку або суми, не показуємо помилку
    if current_state in [BotStates.waiting_for_invoice_text, BotStates.waiting_for_payment_amount]:
        return
    
    await message.answer(
        "❓ Не розумію команду. Використовуйте кнопки меню.",
        reply_markup=get_main_menu()
    )


# Хендлер для невідомих callback'ів
@dp.callback_query()
async def unknown_callback(callback: CallbackQuery):
    """Обробка невідомих callback'ів"""
    await callback.answer("Невідома команда")
    logger.warning(f"Невідомий callback: {callback.data}")


async def main():
    """Основна функція запуску бота"""
    global db
    
    try:
        logger.info("Запуск бота...")
        
        # Ініціалізуємо базу даних
        logger.info("Ініціалізація бази даних...")
        db = initialize_database()
        logger.info("Підключення до Supabase успішно встановлено")
        
        # Видаляємо webhook (якщо був встановлений)
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаємо polling
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Критична помилка: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот зупинено користувачем")
    except Exception as e:
        logger.error(f"Помилка запуску: {e}") 