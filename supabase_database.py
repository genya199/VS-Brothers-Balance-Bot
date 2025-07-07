import logging
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from supabase import create_client, Client
from config import DATE_FORMAT, DATETIME_FORMAT
from utils import calculate_balance_for_operations

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SupabaseDatabase:
    """Клас для роботи з базою даних Supabase"""
    
    def __init__(self):
        """Ініціалізація підключення до Supabase"""
        try:
            # Отримуємо змінні середовища
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_KEY')
            
            if not supabase_url or not supabase_key:
                raise ValueError("SUPABASE_URL та SUPABASE_KEY мають бути встановлені в змінних середовища")
            
            self.supabase: Client = create_client(supabase_url, supabase_key)
            logger.info("Підключення до Supabase успішно встановлено")
            
        except Exception as e:
            logger.error(f"Помилка підключення до Supabase: {e}")
            raise
    
    def add_invoice(self, user_id: int, car_info: str, amount: float, original_text: str) -> bool:
        """
        Додавання нового рахунку
        
        Args:
            user_id: ID користувача в Telegram
            car_info: Інформація про автомобіль
            amount: Сума рахунку
            original_text: Оригінальний текст повідомлення
            
        Returns:
            bool: True якщо успішно додано, False у випадку помилки
        """
        try:
            # Додаємо рахунок
            invoice_data = {
                'user_id': user_id,
                'car_info': car_info,
                'amount': amount,
                'original_text': original_text,
                'date_created': datetime.now().isoformat()
            }
            
            result = self.supabase.table('invoices').insert(invoice_data).execute()
            
            if result.data:
                # Оновлюємо баланс (віднімаємо суму рахунку)
                self._update_balance(user_id, -amount)
                logger.info(f"Рахунок додано для користувача {user_id}: {amount} євро")
                return True
            else:
                logger.error("Помилка додавання рахунку: відсутні дані у відповіді")
                return False
                
        except Exception as e:
            logger.error(f"Помилка додавання рахунку: {e}")
            return False
    
    def add_payment(self, user_id: int, amount: float, date_paid: str, invoice_id: int = None) -> bool:
        """
        Додавання платежу (на баланс або за конкретний рахунок)
        
        Args:
            user_id: ID користувача в Telegram
            amount: Сума платежу
            date_paid: Дата платежу у форматі DD.MM.YYYY
            invoice_id: ID рахунку (опціонально, для платежу за конкретний рахунок)
            
        Returns:
            bool: True якщо успішно додано, False у випадку помилки
        """
        try:
            # Додаємо платіж
            payment_data = {
                'user_id': user_id,
                'amount': amount,
                'date_paid': date_paid,
                'date_created': datetime.now().isoformat()
            }
            
            # Додаємо invoice_id якщо це платіж за рахунок
            if invoice_id is not None:
                payment_data['invoice_id'] = invoice_id
            
            result = self.supabase.table('payments').insert(payment_data).execute()
            
            if result.data:
                # Оновлюємо баланс (додаємо суму платежу)
                self._update_balance(user_id, amount)
                
                # Логування залежно від типу платежу
                if invoice_id is not None:
                    logger.info(f"Платіж {amount} євро додано для рахунку {invoice_id} користувача {user_id}")
                else:
                    logger.info(f"Платіж додано для користувача {user_id}: {amount} євро на {date_paid}")
                return True
            else:
                logger.error("Помилка додавання платежу: відсутні дані у відповіді")
                return False
                
        except Exception as e:
            logger.error(f"Помилка додавання платежу: {e}")
            return False
    
    def get_balance(self, user_id: int) -> float:
        """
        Отримання поточного балансу користувача
        
        Args:
            user_id: ID користувача в Telegram
            
        Returns:
            float: Поточний баланс
        """
        try:
            result = self.supabase.table('balance').select('current_balance').eq('user_id', user_id).execute()
            
            if result.data and len(result.data) > 0:
                return float(result.data[0]['current_balance'])
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"Помилка отримання балансу: {e}")
            return 0.0
    
    def get_history(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Отримання історії операцій
        
        Args:
            user_id: ID користувача в Telegram
            limit: Максимальна кількість записів
            
        Returns:
            List[Dict]: Список операцій з деталями
        """
        try:
            # Отримуємо рахунки
            invoices_result = self.supabase.table('invoices')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date_created', desc=True)\
                .execute()
            
            # Отримуємо платежі з інформацією про рахунки
            payments_result = self.supabase.table('payments')\
                .select('*')\
                .eq('user_id', user_id)\
                .order('date_created', desc=True)\
                .execute()
            
            # Об'єднуємо та сортуємо по даті створення
            history = []
            
            for invoice in invoices_result.data:
                history.append({
                    'type': 'invoice',
                    'id': invoice['id'],
                    'car_info': invoice['car_info'],
                    'amount': -float(invoice['amount']),  # Від'ємна сума для рахунків
                    'date': invoice['date_created'],
                    'original_text': invoice.get('original_text')
                })
            
            for payment in payments_result.data:
                payment_info = {
                    'type': 'payment',
                    'id': payment['id'],
                    'amount': float(payment['amount']),
                    'date_paid': payment.get('date_paid'),
                    'date': payment['date_created'],
                    'invoice_id': payment.get('invoice_id')
                }
                
                # Визначаємо тип платежу та інформацію про авто
                if payment.get('invoice_id'):
                    payment_info['payment_type'] = 'invoice'
                    # Отримуємо інформацію про авто з рахунку
                    try:
                        invoice_result = self.supabase.table('invoices')\
                            .select('car_info')\
                            .eq('id', payment['invoice_id'])\
                            .execute()
                        
                        if invoice_result.data:
                            payment_info['car_info'] = invoice_result.data[0]['car_info']
                    except:
                        # Якщо не вдалося отримати інформацію про рахунок
                        pass
                else:
                    payment_info['payment_type'] = 'balance'
                
                history.append(payment_info)
            
            # Сортуємо по даті створення (найновіші спочатку)
            history.sort(key=lambda x: x['date'], reverse=True)
            
            return history[:limit]
            
        except Exception as e:
            logger.error(f"Помилка отримання історії: {e}")
            return []
    
    def get_last_operation(self, user_id: int) -> Optional[Dict]:
        """
        Отримання останньої операції користувача
        
        Args:
            user_id: ID користувача в Telegram
            
        Returns:
            Optional[Dict]: Деталі останньої операції або None
        """
        history = self.get_history(user_id, limit=1)
        return history[0] if history else None
    
    def delete_last_operation(self, user_id: int) -> bool:
        """
        Видалення останньої операції (для функції "скасувати")
        
        Args:
            user_id: ID користувача в Telegram
            
        Returns:
            bool: True якщо успішно видалено, False у випадку помилки
        """
        try:
            # Знаходимо останню операцію
            last_invoice_result = self.supabase.table('invoices')\
                .select('id, amount, date_created')\
                .eq('user_id', user_id)\
                .order('date_created', desc=True)\
                .limit(1)\
                .execute()
            
            last_payment_result = self.supabase.table('payments')\
                .select('id, amount, date_created')\
                .eq('user_id', user_id)\
                .order('date_created', desc=True)\
                .limit(1)\
                .execute()
            
            last_invoice = last_invoice_result.data[0] if last_invoice_result.data else None
            last_payment = last_payment_result.data[0] if last_payment_result.data else None
            
            # Визначаємо, яка операція була останньою
            if last_invoice and last_payment:
                if last_invoice['date_created'] > last_payment['date_created']:
                    # Видаляємо рахунок
                    self.supabase.table('invoices').delete().eq('id', last_invoice['id']).execute()
                    self._update_balance(user_id, float(last_invoice['amount']))  # Повертаємо суму
                else:
                    # Видаляємо платіж
                    self.supabase.table('payments').delete().eq('id', last_payment['id']).execute()
                    self._update_balance(user_id, -float(last_payment['amount']))  # Віднімаємо суму
                    
            elif last_invoice:
                self.supabase.table('invoices').delete().eq('id', last_invoice['id']).execute()
                self._update_balance(user_id, float(last_invoice['amount']))
                
            elif last_payment:
                self.supabase.table('payments').delete().eq('id', last_payment['id']).execute()
                self._update_balance(user_id, -float(last_payment['amount']))
                
            else:
                return False  # Немає операцій для видалення
            
            return True
            
        except Exception as e:
            logger.error(f"Помилка видалення останньої операції: {e}")
            return False
    
    def export_history(self, user_id: int) -> str:
        """
        Експорт історії операцій у текстовому форматі
        
        Args:
            user_id: ID користувача в Telegram
            
        Returns:
            str: Форматований текст з історією
        """
        history = self.get_history(user_id)
        
        if not history:
            return "Історія операцій порожня."
        
        export_text = "📋 ІСТОРІЯ ОПЕРАЦІЙ\n"
        export_text += "=" * 35 + "\n\n"
        
        # Сортуємо історію за датою (від старіших до новіших для хронології)
        sorted_history = sorted(history, key=lambda x: x.get('date', ''), reverse=False)
        
        # Розраховуємо баланс після кожної операції
        balance_history = calculate_balance_for_operations(sorted_history)
        
        operation_count = 0
        
        for operation in sorted_history:
            operation_count += 1
            
            # Форматуємо дату у зрозумілому форматі
            date_str = operation.get('date', '')
            if 'T' in date_str:
                # Конвертуємо ISO формат у звичайний
                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                formatted_date = date_obj.strftime('%d.%m.%Y')
            else:
                formatted_date = date_str
            
            # Отримуємо баланс після цієї операції
            operation_key = f"{operation.get('type', '')}_{operation.get('id', '')}"
            balance_after_op = balance_history.get(operation_key, 0.0)
            
            if operation['type'] == 'payment':
                # ПЛАТІЖ (за рахунок або поповнення балансу)
                export_text += f"— ПЛАТІЖ #{operation_count}\n"
                export_text += f"💰 Сума: +{operation['amount']:.2f} євро\n"
                export_text += f"📅 Дата платежу: {formatted_date}\n"
                
                # Визначаємо тип платежу
                payment_type = operation.get('payment_type', 'balance')
                if payment_type == 'invoice':
                    # Платіж за конкретний рахунок
                    car_info = operation.get('car_info', 'Невідоме авто')
                    export_text += f"🎯 Тип: Платіж за рахунок\n"
                    export_text += f"🚗 Авто: {car_info}\n"
                else:
                    # Поповнення балансу
                    export_text += f"🎯 Тип: Платіж на баланс\n"
                
                export_text += f"📊 Баланс після операції: {balance_after_op:+.2f} євро\n"
                
            else:  # invoice
                # РАХУНОК ЗА ПОСЛУГИ
                export_text += f"— РАХУНОК #{operation_count}\n"
                car_info = operation.get('car_info', 'Не вказано')
                export_text += f"🚗 Авто: {car_info}\n"
                export_text += f"💰 Сума: {operation['amount']:.2f} євро\n"
                export_text += f"📅 Дата створення: {formatted_date}\n"
                export_text += f"📊 Баланс після операції: {balance_after_op:+.2f} євро\n"
            
            export_text += "-" * 35 + "\n\n"
        
        # Підсумок
        current_balance = self.get_balance(user_id)
        export_text += f"💰 ПІДСУМОК:\n"
        export_text += f"📊 Поточний баланс: {current_balance:+.2f} євро\n"
        if current_balance >= 0:
            export_text += f"✅ Стан: Позитивний баланс\n"
        else:
            export_text += f"❌ Стан: Борг {abs(current_balance):.2f} євро\n"
        
        export_text += f"\n📅 Звіт згенеровано: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
        export_text += f"👤 Загальна кількість операцій: {operation_count}"
        
        return export_text
    
    def get_paginated_history(self, user_id: int, page: int = 1, per_page: int = 5) -> Tuple[List[Dict], int, int]:
        """
        Отримання історії операцій з пагінацією для видалення
        
        Args:
            user_id: ID користувача в Telegram
            page: Номер сторінки (починаючи з 1)
            per_page: Кількість записів на сторінку
            
        Returns:
            Tuple: (операції, загальна_кількість, загальна_кількість_сторінок)
        """
        try:
            # Підраховуємо загальну кількість операцій
            invoices_count = self.supabase.table('invoices')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            payments_count = self.supabase.table('payments')\
                .select('id', count='exact')\
                .eq('user_id', user_id)\
                .execute()
            
            total_count = invoices_count.count + payments_count.count
            total_pages = (total_count + per_page - 1) // per_page
            
            if total_count == 0:
                return [], 0, 0
            
            # Отримуємо всі операції та сортуємо їх
            history = self.get_history(user_id, limit=1000)  # Отримуємо всі операції
            
            # Застосовуємо пагінацію
            start_index = (page - 1) * per_page
            end_index = start_index + per_page
            paginated_history = history[start_index:end_index]
            
            return paginated_history, total_count, total_pages
            
        except Exception as e:
            logger.error(f"Помилка отримання історії з пагінацією: {e}")
            return [], 0, 0
    
    def delete_invoice_by_id(self, user_id: int, invoice_id: int) -> bool:
        """
        Видалення конкретного рахунку за ID
        
        Args:
            user_id: ID користувача в Telegram
            invoice_id: ID рахунку для видалення
            
        Returns:
            bool: True якщо успішно видалено, False у випадку помилки
        """
        try:
            # Спочатку отримуємо інформацію про рахунок для оновлення балансу
            invoice_result = self.supabase.table('invoices')\
                .select('amount')\
                .eq('id', invoice_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not invoice_result.data:
                logger.warning(f"Рахунок {invoice_id} не знайдено для користувача {user_id}")
                return False
            
            amount = float(invoice_result.data[0]['amount'])
            
            # Видаляємо рахунок
            delete_result = self.supabase.table('invoices')\
                .delete()\
                .eq('id', invoice_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if delete_result.data is not None:
                # Оновлюємо баланс (повертаємо суму рахунку)
                self._update_balance(user_id, amount)
                logger.info(f"Рахунок {invoice_id} видалено для користувача {user_id}")
                return True
            else:
                logger.error(f"Помилка видалення рахунку {invoice_id}")
                return False
                
        except Exception as e:
            logger.error(f"Помилка видалення рахунку: {e}")
            return False
    
    def delete_payment_by_id(self, user_id: int, payment_id: int) -> bool:
        """
        Видалення конкретного платежу за ID
        
        Args:
            user_id: ID користувача в Telegram
            payment_id: ID платежу для видалення
            
        Returns:
            bool: True якщо успішно видалено, False у випадку помилки
        """
        try:
            # Спочатку отримуємо інформацію про платіж для оновлення балансу
            payment_result = self.supabase.table('payments')\
                .select('amount')\
                .eq('id', payment_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not payment_result.data:
                logger.warning(f"Платіж {payment_id} не знайдено для користувача {user_id}")
                return False
            
            amount = float(payment_result.data[0]['amount'])
            
            # Видаляємо платіж
            delete_result = self.supabase.table('payments')\
                .delete()\
                .eq('id', payment_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if delete_result.data is not None:
                # Оновлюємо баланс (віднімаємо суму платежу)
                self._update_balance(user_id, -amount)
                logger.info(f"Платіж {payment_id} видалено для користувача {user_id}")
                return True
            else:
                logger.error(f"Помилка видалення платежу {payment_id}")
                return False
                
        except Exception as e:
            logger.error(f"Помилка видалення платежу: {e}")
            return False
    
    def get_unpaid_invoices(self, user_id: int) -> List[Dict]:
        """
        Отримання списку всіх рахунків користувача
        
        Args:
            user_id: ID користувача в Telegram
            
        Returns:
            List[Dict]: Список рахунків з деталями
        """
        try:
            result = self.supabase.table('invoices')\
                .select('id, car_info, amount, date_created')\
                .eq('user_id', user_id)\
                .order('date_created', desc=True)\
                .execute()
            
            if result.data:
                invoices = []
                for invoice in result.data:
                    invoices.append({
                        'id': invoice['id'],
                        'car_info': invoice['car_info'],
                        'amount': float(invoice['amount']),
                        'date_created': invoice['date_created'][:10] if invoice['date_created'] else '',
                        'display_text': f"{invoice['car_info'][:30]}{'...' if len(invoice['car_info']) > 30 else ''} - {float(invoice['amount']):.2f}€"
                    })
                return invoices
            else:
                return []
                
        except Exception as e:
            logger.error(f"Помилка отримання рахунків: {e}")
            return []
    
    def get_recent_invoices(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Отримання останніх N рахунків користувача
        
        Args:
            user_id: ID користувача в Telegram
            limit: Кількість останніх рахунків (за замовчуванням 5)
            
        Returns:
            List[Dict]: Список останніх рахунків з деталями
        """
        try:
            result = self.supabase.table('invoices')\
                .select('id, car_info, amount, date_created')\
                .eq('user_id', user_id)\
                .order('date_created', desc=True)\
                .limit(limit)\
                .execute()
            
            if result.data:
                invoices = []
                for invoice in result.data:
                    invoices.append({
                        'id': invoice['id'],
                        'car_info': invoice['car_info'],
                        'amount': float(invoice['amount']),
                        'date_created': invoice['date_created'][:10] if invoice['date_created'] else '',
                        'display_text': f"{invoice['car_info'][:30]}{'...' if len(invoice['car_info']) > 30 else ''} - {float(invoice['amount']):.2f}€"
                    })
                return invoices
            else:
                return []
                
        except Exception as e:
            logger.error(f"Помилка отримання останніх рахунків: {e}")
            return []
    
    def add_payment_for_invoice(self, user_id: int, invoice_id: int, amount: float, date_paid: str) -> bool:
        """
        Додавання платежу для конкретного рахунку
        
        Args:
            user_id: ID користувача в Telegram
            invoice_id: ID рахунку за який здійснюється платіж
            amount: Сума платежу
            date_paid: Дата платежу у форматі DD.MM.YYYY
            
        Returns:
            bool: True якщо успішно додано, False у випадку помилки
        """
        try:
            # Отримуємо інформацію про рахунок
            invoice_result = self.supabase.table('invoices')\
                .select('car_info, amount')\
                .eq('id', invoice_id)\
                .eq('user_id', user_id)\
                .execute()
            
            if not invoice_result.data:
                logger.error(f"Рахунок {invoice_id} не знайдено")
                return False
            
            invoice_info = invoice_result.data[0]
            
            # Додаємо платіж з інформацією про рахунок
            payment_data = {
                'user_id': user_id,
                'amount': amount,
                'date_paid': date_paid,
                'date_created': datetime.now().isoformat(),
                'invoice_id': invoice_id,  # Зв'язуємо з рахунком
                'car_info': invoice_info['car_info']  # Додаємо інформацію про авто для зручності
            }
            
            result = self.supabase.table('payments').insert(payment_data).execute()
            
            if result.data:
                # Оновлюємо баланс (додаємо суму платежу)
                self._update_balance(user_id, amount)
                logger.info(f"Платіж {amount} євро додано для рахунку {invoice_id} користувача {user_id}")
                return True
            else:
                logger.error("Помилка додавання платежу для рахунку: відсутні дані у відповіді")
                return False
                
        except Exception as e:
            logger.error(f"Помилка додавання платежу для рахунку: {e}")
            return False
    
    def _update_balance(self, user_id: int, amount: float):
        """
        Оновлення балансу користувача
        
        Args:
            user_id: ID користувача
            amount: Сума для зміни балансу (+ або -)
        """
        try:
            # Перевіряємо, чи існує запис балансу
            balance_result = self.supabase.table('balance')\
                .select('current_balance')\
                .eq('user_id', user_id)\
                .execute()
            
            if balance_result.data:
                # Оновлюємо існуючий баланс
                current_balance = float(balance_result.data[0]['current_balance'])
                new_balance = current_balance + amount
                
                self.supabase.table('balance')\
                    .update({
                        'current_balance': new_balance,
                        'last_updated': datetime.now().isoformat()
                    })\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                # Створюємо новий запис балансу
                self.supabase.table('balance')\
                    .insert({
                        'user_id': user_id,
                        'current_balance': amount,
                        'last_updated': datetime.now().isoformat()
                    })\
                    .execute()
                    
        except Exception as e:
            logger.error(f"Помилка оновлення балансу: {e}")


# Глобальний об'єкт бази даних (ініціалізується пізніше)
db = None

def initialize_database():
    """Ініціалізація глобального об'єкта бази даних"""
    global db
    if db is None:
        db = SupabaseDatabase()
    return db 