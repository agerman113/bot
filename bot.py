import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import os
import json
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение данных из переменных окружения
GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
GROUP_ID = os.getenv('VK_GROUP_ID')

# ID администраторов (ваш ID VK)
ADMIN_IDS = [153444476]  # ЗАМЕНИТЕ НА ВАШ РЕАЛЬНЫЙ ID VK

class TelemarketingBot:
    def __init__(self):
        self.db = sqlite3.connect('telemarketing.db', check_same_thread=False)
        self.init_database()
        self.create_test_numbers()
    
    def init_database(self):
        """Инициализация базы данных"""
        cursor = self.db.cursor()
        
        # Таблица номеров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS phone_numbers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                phone TEXT UNIQUE,
                company TEXT,
                contact_name TEXT,
                description TEXT,
                status TEXT DEFAULT 'new',
                manager_id INTEGER,
                manager_name TEXT,
                call_result TEXT,
                call_notes TEXT,
                call_time TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица менеджеров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS managers (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                full_name TEXT,
                calls_total INTEGER DEFAULT 0,
                calls_success INTEGER DEFAULT 0,
                calls_callback INTEGER DEFAULT 0,
                calls_rejected INTEGER DEFAULT 0,
                earnings REAL DEFAULT 0,
                last_active TIMESTAMP,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Таблица выплат
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                manager_id INTEGER,
                amount REAL,
                status TEXT DEFAULT 'pending',
                payment_date TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        self.db.commit()
        logger.info("База данных инициализирована")
    
    def create_test_numbers(self):
        """Создание тестовой базы из 3 номеров"""
        cursor = self.db.cursor()
        
        test_numbers = [
            ('+7 (999) 111-22-33', 'ООО "Ромашка"', 'Иван Петров', 'Директор по развитию'),
            ('+7 (999) 222-33-44', 'ИП "Солнышко"', 'Мария Иванова', 'Менеджер по закупкам'),
            ('+7 (999) 333-44-55', 'ЗАО "Весна"', 'Алексей Сидоров', 'Руководитель отдела')
        ]
        
        for phone, company, contact, desc in test_numbers:
            cursor.execute('''
                INSERT OR IGNORE INTO phone_numbers (phone, company, contact_name, description)
                VALUES (?, ?, ?, ?)
            ''', (phone, company, contact, desc))
        
        self.db.commit()
        logger.info(f"Добавлено {len(test_numbers)} тестовых номеров")
    
    def add_new_numbers(self, numbers_list):
        """Добавить новые номера в базу"""
        cursor = self.db.cursor()
        added = 0
        
        for phone, company, contact, desc in numbers_list:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO phone_numbers (phone, company, contact_name, description)
                    VALUES (?, ?, ?, ?)
                ''', (phone, company, contact, desc))
                added += 1
            except:
                continue
        
        self.db.commit()
        return added
    
    def get_next_number(self, manager_id, manager_name):
        """Получить следующий номер для звонка"""
        cursor = self.db.cursor()
        
        # Ищем номер, который этот менеджер еще не звонил
        cursor.execute('''
            SELECT id, phone, company, contact_name, description
            FROM phone_numbers 
            WHERE status = 'new' 
            AND id NOT IN (
                SELECT id FROM phone_numbers WHERE manager_id = ?
            )
            ORDER BY RANDOM()
            LIMIT 1
        ''', (manager_id,))
        
        number = cursor.fetchone()
        
        if number:
            # Помечаем как "в работе"
            cursor.execute('''
                UPDATE phone_numbers 
                SET status = 'in_progress', manager_id = ?, manager_name = ?
                WHERE id = ?
            ''', (manager_id, manager_name, number[0]))
            self.db.commit()
            
            return {
                'id': number[0],
                'phone': number[1],
                'company': number[2],
                'contact': number[3],
                'description': number[4]
            }
        
        return None
    
    def save_report(self, manager_id, number_id, result, notes=""):
        """Сохранить отчет о звонке"""
        cursor = self.db.cursor()
        
        # Обновляем статус номера
        cursor.execute('''
            UPDATE phone_numbers 
            SET status = ?, call_result = ?, call_notes = ?, call_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (result, result, notes, number_id))
        
        # Обновляем статистику менеджера
        cursor.execute('''
            INSERT OR REPLACE INTO managers 
            (user_id, calls_total, calls_success, calls_callback, calls_rejected, last_active)
            VALUES (?, 
                COALESCE((SELECT calls_total FROM managers WHERE user_id = ?), 0) + 1,
                COALESCE((SELECT calls_success FROM managers WHERE user_id = ?), 0) + ?,
                COALESCE((SELECT calls_callback FROM managers WHERE user_id = ?), 0) + ?,
                COALESCE((SELECT calls_rejected FROM managers WHERE user_id = ?), 0) + ?,
                CURRENT_TIMESTAMP
            )
        ''', (manager_id, manager_id, manager_id, 
              1 if result == 'success' else 0,
              manager_id, 1 if result == 'callback' else 0,
              manager_id, 1 if result == 'rejected' else 0))
        
        # Начисляем деньги за успешный звонок
        if result == 'success':
            cursor.execute('''
                UPDATE managers 
                SET earnings = COALESCE(earnings, 0) + 50
                WHERE user_id = ?
            ''', (manager_id,))
        
        self.db.commit()
        return True
    
    # ==================== АДМИН ФУНКЦИИ ====================
    
    def get_admin_stats(self):
        """Получить общую статистику для админа"""
        cursor = self.db.cursor()
        
        # Общая статистика
        cursor.execute('''
            SELECT 
                COUNT(*) as total_numbers,
                SUM(CASE WHEN status = 'called' THEN 1 ELSE 0 END) as called,
                SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new,
                SUM(CASE WHEN status = 'callback' THEN 1 ELSE 0 END) as callback,
                COUNT(DISTINCT manager_id) as active_managers
            FROM phone_numbers
        ''')
        
        stats = cursor.fetchone()
        
        # Статистика по менеджерам
        cursor.execute('''
            SELECT 
                COUNT(*) as total_managers,
                SUM(calls_total) as total_calls,
                SUM(calls_success) as success_calls,
                SUM(earnings) as total_earnings
            FROM managers
        ''')
        
        manager_stats = cursor.fetchone()
        
        return {
            'total_numbers': stats[0],
            'called': stats[1],
            'new': stats[2],
            'callback': stats[3],
            'active_managers': stats[4],
            'total_managers': manager_stats[0],
            'total_calls': manager_stats[1],
            'success_calls': manager_stats[2],
            'total_earnings': manager_stats[3]
        }
    
    def get_recent_reports(self, limit=20):
        """Получить последние отчеты"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT 
                p.phone, p.company, p.contact_name,
                p.call_result, p.call_time, p.manager_name,
                p.call_notes
            FROM phone_numbers p
            WHERE p.status != 'new' AND p.status != 'in_progress'
            ORDER BY p.call_time DESC
            LIMIT ?
        ''', (limit,))
        
        return cursor.fetchall()
    
    def get_manager_details(self, manager_id=None):
        """Получить детальную информацию по менеджерам"""
        cursor = self.db.cursor()
        
        if manager_id:
            cursor.execute('''
                SELECT 
                    user_id, full_name, calls_total, calls_success,
                    calls_callback, calls_rejected, earnings, last_active
                FROM managers 
                WHERE user_id = ?
            ''', (manager_id,))
        else:
            cursor.execute('''
                SELECT 
                    user_id, full_name, calls_total, calls_success,
                    calls_callback, calls_rejected, earnings, last_active
                FROM managers 
                ORDER BY calls_success DESC
                LIMIT 10
            ''')
        
        return cursor.fetchall()
    
    def get_numbers_report(self, status=None):
        """Получить отчет по номерам"""
        cursor = self.db.cursor()
        
        if status:
            cursor.execute('''
                SELECT phone, company, contact_name, status, 
                       call_time, manager_name, call_result
                FROM phone_numbers 
                WHERE status = ?
                ORDER BY id DESC
            ''', (status,))
        else:
            cursor.execute('''
                SELECT phone, company, contact_name, status, 
                       call_time, manager_name, call_result
                FROM phone_numbers 
                ORDER BY status, id DESC
            ''')
        
        return cursor.fetchall()
    
    def reset_number_status(self, phone, new_status='new'):
        """Сбросить статус номера"""
        cursor = self.db.cursor()
        cursor.execute('''
            UPDATE phone_numbers 
            SET status = ?, manager_id = NULL, manager_name = NULL,
                call_result = NULL, call_notes = NULL, call_time = NULL
            WHERE phone = ?
        ''', (new_status, phone))
        
        self.db.commit()
        return cursor.rowcount > 0

# Инициализация бота
bot = TelemarketingBot()

def is_admin(user_id):
    """Проверка, является ли пользователь администратором"""
    return user_id in ADMIN_IDS

def format_report(reports):
    """Форматировать отчет для отправки"""
    if not reports:
        return "Нет данных для отчета"
    
    result = "📋 **ОТЧЕТ:**\n\n"
    for i, report in enumerate(reports, 1):
        if len(report) >= 6:
            result += f"{i}. 📞 {report[0]}\n"
            result += f"   🏢 {report[1]}\n"
            result += f"   👤 {report[2]}\n"
            result += f"   📊 Статус: {report[3]}\n"
            if report[4]:
                result += f"   ⏰ Время: {report[4]}\n"
            if report[5]:
                result += f"   👨‍💼 Менеджер: {report[5]}\n"
            if len(report) > 6 and report[6]:
                result += f"   💬 Заметки: {report[6]}\n"
            result += "\n"
    
    return result

def main():
    if not GROUP_TOKEN or not GROUP_ID:
        logger.error("Не установлены переменные окружения VK_GROUP_TOKEN и VK_GROUP_ID!")
        return
    
    # Замените ADMIN_IDS на ваш реальный ID
    global ADMIN_IDS
    if ADMIN_IDS[0] == 123456789:
        logger.warning("Замените ADMIN_IDS на ваш реальный ID VK!")
    
    try:
        vk_session = vk_api.VkApi(token=GROUP_TOKEN)
        vk = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, GROUP_ID)
        
        logger.info(f"Бот телемаркетинга запущен для группы ID: {GROUP_ID}")
        
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                message = event.obj.message
                user_id = message['from_id']
                text = message['text'].lower() if 'text' in message else ''
                
                logger.info(f"Сообщение от {user_id}: {text}")
                
                # ==================== КОМАНДЫ ДЛЯ ВСЕХ ====================
                
                # Команда: начало работы
                if text in ['начать', 'старт', 'работа', 'start']:
                    # Получаем имя пользователя
                    user_info = vk.users.get(user_ids=user_id, fields='first_name,last_name')[0]
                    user_name = f"{user_info['first_name']} {user_info['last_name']}"
                    
                    # Регистрируем менеджера
                    cursor = bot.db.cursor()
                    cursor.execute('''
                        INSERT OR IGNORE INTO managers (user_id, full_name)
                        VALUES (?, ?)
                    ''', (user_id, user_name))
                    bot.db.commit()
                    
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_button('📞 Получить номер', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('📊 Моя статистика', color=VkKeyboardColor.PRIMARY)
                    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
                    
                    response = (
                        f"👋 Привет, {user_info['first_name']}!\n"
                        "🏢 Добро пожаловать в систему телемаркетинга!\n\n"
                        "📞 **Как это работает:**\n"
                        "1. Получаете номер компании для звонка\n"
                        "2. Звоните по готовому скрипту\n"
                        "3. Отправляете отчет о результате\n"
                        "4. Получаете новые номера\n\n"
                        "💰 **Выплаты:** каждый успешный контакт = 50 руб\n\n"
                        "Нажмите '📞 Получить номер' для начала!"
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=keyboard.get_keyboard(),
                        random_id=0
                    )
                
                # Команда: получить номер
                elif 'получить номер' in text or text == 'номер':
                    user_info = vk.users.get(user_ids=user_id, fields='first_name')[0]
                    user_name = user_info['first_name']
                    
                    number_data = bot.get_next_number(user_id, user_name)
                    
                    if number_data:
                        keyboard = VkKeyboard(one_time=False)
                        keyboard.add_button('✅ Успешно', color=VkKeyboardColor.POSITIVE)
                        keyboard.add_button('📅 Перезвонить', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_line()
                        keyboard.add_button('❌ Отказ', color=VkKeyboardColor.NEGATIVE)
                        keyboard.add_button('🚫 Неверный номер', color=VkKeyboardColor.SECONDARY)
                        
                        script = (
                            "📞 **СКРИПТ ДЛЯ ЗВОНКА:**\n\n"
                            "1. 'Добрый день! Это [ваше имя] из сервиса удаленного телемаркетинга.'\n"
                            "2. 'По поводу развития вашего бизнеса.'\n"
                            "3. 'Мы помогаем компаниям увеличивать продажи через удаленных специалистов.'\n"
                            "4. 'Можем выделить вам менеджера от 500 руб/час.'\n"
                            "5. 'Предлагаем тестовый день - 2 часа за наш счет.'"
                        )
                        
                        response = (
                            f"📞 **НОМЕР ДЛЯ ЗВОНКА:**\n"
                            f"━━━━━━━━━━━━━━━━━\n"
                            f"🏢 Компания: {number_data['company']}\n"
                            f"👤 Контакт: {number_data['contact']}\n"
                            f"📱 Телефон: {number_data['phone']}\n"
                            f"📝 {number_data['description']}\n"
                            f"━━━━━━━━━━━━━━━━━\n\n"
                            f"{script}\n\n"
                            f"**После звонка нажмите одну из кнопок:**"
                        )
                    else:
                        response = "😔 На данный момент нет доступных номеров.\nПопробуйте позже."
                        keyboard = None
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=keyboard.get_keyboard() if keyboard else None,
                        random_id=0
                    )
                
                # Обработка результатов звонка
                elif text in ['успешно', 'перезвонить', 'отказ', 'неверный номер']:
                    cursor = bot.db.cursor()
                    cursor.execute('''
                        SELECT id FROM phone_numbers 
                        WHERE manager_id = ? AND status = 'in_progress'
                        ORDER BY id DESC LIMIT 1
                    ''', (user_id,))
                    
                    last_number = cursor.fetchone()
                    
                    if last_number:
                        number_id = last_number[0]
                        
                        if text == 'успешно':
                            result = 'success'
                            notes = "Успешный контакт"
                        elif text == 'перезвонить':
                            result = 'callback'
                            notes = "Нужно перезвонить"
                        elif text == 'отказ':
                            result = 'rejected'
                            notes = "Клиент отказался"
                        else:  # неверный номер
                            result = 'invalid'
                            notes = "Неверный номер"
                        
                        # Сохраняем отчет
                        bot.save_report(user_id, number_id, result, notes)
                        
                        # Получаем статистику менеджера
                        cursor.execute('''
                            SELECT calls_total, calls_success, earnings 
                            FROM managers WHERE user_id = ?
                        ''', (user_id,))
                        
                        stats = cursor.fetchone()
                        
                        if stats:
                            calls_total, calls_success, earnings = stats
                            response = (
                                f"✅ Отчет сохранен!\n\n"
                                f"📊 Ваша статистика:\n"
                                f"━━━━━━━━━━━━━━━━━\n"
                                f"📞 Всего звонков: {calls_total}\n"
                                f"✅ Успешных: {calls_success}\n"
                                f"💰 Заработано: {earnings} руб\n"
                                f"━━━━━━━━━━━━━━━━━\n\n"
                                f"Хотите получить следующий номер?"
                            )
                        else:
                            response = "✅ Отчет сохранен! Хотите получить следующий номер?"
                        
                        keyboard = VkKeyboard(one_time=False)
                        keyboard.add_button('📞 Следующий номер', color=VkKeyboardColor.POSITIVE)
                        keyboard.add_button('📊 Моя статистика', color=VkKeyboardColor.PRIMARY)
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            keyboard=keyboard.get_keyboard(),
                            random_id=0
                        )
                    else:
                        vk.messages.send(
                            user_id=user_id,
                            message="❌ Не найден активный номер для отчета.",
                            random_id=0
                        )
                
                # Команда: моя статистика
                elif 'моя статистика' in text or 'статистика' in text:
                    cursor = bot.db.cursor()
                    cursor.execute('''
                        SELECT calls_total, calls_success, calls_callback, 
                               calls_rejected, earnings, last_active
                        FROM managers WHERE user_id = ?
                    ''', (user_id,))
                    
                    stats = cursor.fetchone()
                    
                    if stats:
                        calls_total, calls_success, calls_callback, calls_rejected, earnings, last_active = stats
                        
                        success_rate = (calls_success / calls_total * 100) if calls_total > 0 else 0
                        
                        response = (
                            f"📊 **ВАША СТАТИСТИКА:**\n"
                            f"━━━━━━━━━━━━━━━━━\n"
                            f"📞 Всего звонков: {calls_total}\n"
                            f"✅ Успешных: {calls_success}\n"
                            f"📅 На перезвон: {calls_callback}\n"
                            f"❌ Отказов: {calls_rejected}\n"
                            f"📈 Конверсия: {success_rate:.1f}%\n"
                            f"💰 Заработано: {earnings} руб\n"
                            f"⏰ Последняя активность: {last_active}\n"
                            f"━━━━━━━━━━━━━━━━━\n\n"
                            f"💡 Совет: Делайте больше звонков,\n"
                            f"чтобы увеличить доход!"
                        )
                    else:
                        response = "У вас еще нет статистики. Сделайте первый звонок!"
                    
                    vk.messages.send(user_id=user_id, message=response, random_id=0)
                
                # Команда: помощь
                elif 'помощь' in text:
                    response = (
                        "❓ **ПОМОЩЬ:**\n\n"
                        "📞 **Для работы:**\n"
                        "1. Нажмите '📞 Получить номер'\n"
                        "2. Позвоните по скрипту\n"
                        "3. Выберите результат:\n"
                        "   • ✅ Успешно - клиент заинтересован\n"
                        "   • 📅 Перезвонить - клиент занят\n"
                        "   • ❌ Отказ - клиент отказался\n"
                        "   • 🚫 Неверный номер - ошибка\n\n"
                        "💰 **Оплата:** 50 руб за каждый ✅ Успешно\n"
                        "💳 Выплаты по понедельникам\n\n"
                        "📊 **Команды:**\n"
                        "• '📞 Получить номер' - новый звонок\n"
                        "• '📊 Моя статистика' - ваши результаты\n"
                        "• '❓ Помощь' - эта инструкция"
                    )
                    
                    if is_admin(user_id):
                        response += "\n\n👑 **АДМИН КОМАНДЫ:**\n"
                        response += "• /admin stats - общая статистика\n"
                        response += "• /admin reports - последние отчеты\n"
                        response += "• /admin managers - топ менеджеров\n"
                        response += "• /admin numbers - все номера\n"
                        response += "• /admin add <номер> <компания> <контакт>\n"
                        response += "• /admin reset <номер> - сбросить статус"
                    
                    vk.messages.send(user_id=user_id, message=response, random_id=0)
                
                # ==================== АДМИН КОМАНДЫ ====================
                
                elif text.startswith('/admin') and is_admin(user_id):
                    parts = text.split(' ')
                    
                    if len(parts) == 1:
                        # Меню админа
                        keyboard = VkKeyboard(one_time=False)
                        keyboard.add_button('/admin stats', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('/admin reports', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_line()
                        keyboard.add_button('/admin managers', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_button('/admin numbers', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_line()
                        keyboard.add_button('/admin help', color=VkKeyboardColor.SECONDARY)
                        
                        response = (
                            "👑 **ПАНЕЛЬ АДМИНИСТРАТОРА**\n\n"
                            "Выберите команду:\n"
                            "• /admin stats - общая статистика\n"
                            "• /admin reports - последние отчеты\n"
                            "• /admin managers - топ менеджеров\n"
                            "• /admin numbers - все номера\n"
                            "• /admin add - добавить номера\n"
                            "• /admin reset - сбросить номер\n"
                            "• /admin help - все команды"
                        )
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            keyboard=keyboard.get_keyboard(),
                            random_id=0
                        )
                    
                    elif 'stats' in text:
                        # Общая статистика
                        stats = bot.get_admin_stats()
                        
                        response = (
                            "📊 **ОБЩАЯ СТАТИСТИКА**\n"
                            "━━━━━━━━━━━━━━━━━\n"
                            f"📞 Всего номеров: {stats['total_numbers']}\n"
                            f"✅ Прозвонено: {stats['called']}\n"
                            f"🆕 Новых: {stats['new']}\n"
                            f"📅 На перезвон: {stats['callback']}\n"
                            f"👥 Активных менеджеров: {stats['active_managers']}\n"
                            f"━━━━━━━━━━━━━━━━━\n"
                            f"👨‍💼 Всего менеджеров: {stats['total_managers']}\n"
                            f"📞 Всего звонков: {stats['total_calls']}\n"
                            f"✅ Успешных звонков: {stats['success_calls']}\n"
                            f"💰 Всего выплат: {stats['total_earnings']} руб\n"
                            f"━━━━━━━━━━━━━━━━━\n"
                            f"⏰ Дата: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                        )
                        
                        vk.messages.send(user_id=user_id, message=response, random_id=0)
                    
                    elif 'reports' in text:
                        # Последние отчеты
                        limit = 15
                        if len(parts) > 2 and parts[2].isdigit():
                            limit = int(parts[2])
                        
                        reports = bot.get_recent_reports(limit)
                        response = format_report(reports)
                        
                        # Разбиваем на части, если слишком длинное
                        if len(response) > 4000:
                            parts_response = [response[i:i+4000] for i in range(0, len(response), 4000)]
                            for part in parts_response:
                                vk.messages.send(user_id=user_id, message=part, random_id=0)
                        else:
                            vk.messages.send(user_id=user_id, message=response, random_id=0)
                    
                    elif 'managers' in text:
                        # Топ менеджеров
                        managers = bot.get_manager_details()
                        
                        response = "👑 **ТОП МЕНЕДЖЕРОВ**\n\n"
                        for i, (mgr_id, name, total, success, callback, rejected, earnings, last_active) in enumerate(managers, 1):
                            response += f"{i}. {name}\n"
                            response += f"   📞 {total} звонков | ✅ {success} успешных\n"
                            response += f"   💰 {earnings} руб | ⏰ {last_active}\n\n"
                        
                        vk.messages.send(user_id=user_id, message=response, random_id=0)
                    
                    elif 'numbers' in text:
                        # Все номера
                        status_filter = None
                        if len(parts) > 2:
                            status_filter = parts[2]
                        
                        numbers = bot.get_numbers_report(status_filter)
                        
                        response = "📋 **ВСЕ НОМЕРА**\n\n"
                        for i, (phone, company, contact, status, call_time, manager, result) in enumerate(numbers[:20], 1):
                            response += f"{i}. {phone}\n"
                            response += f"   🏢 {company}\n"
                            response += f"   👤 {contact}\n"
                            response += f"   📊 {status}"
                            if manager:
                                response += f" | 👨‍💼 {manager}"
                            if call_time:
                                response += f" | ⏰ {call_time}\n"
                            else:
                                response += "\n"
                            response += "\n"
                        
                        if len(numbers) > 20:
                            response += f"\n... и еще {len(numbers) - 20} номеров"
                        
                        vk.messages.send(user_id=user_id, message=response, random_id=0)
                    
                    elif 'add' in text and len(parts) >= 5:
                        # Добавить номер вручную
                        try:
                            phone = parts[2]
                            company = parts[3]
                            contact = ' '.join(parts[4:])
                            
                            cursor = bot.db.cursor()
                            cursor.execute('''
                                INSERT OR IGNORE INTO phone_numbers (phone, company, contact_name)
                                VALUES (?, ?, ?)
                            ''', (phone, company, contact))
                            bot.db.commit()
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=f"✅ Номер добавлен: {phone}",
                                random_id=0
                            )
                        except:
                            vk.messages.send(
                                user_id=user_id,
                                message="❌ Ошибка добавления номера",
                                random_id=0
                            )
                    
                    elif 'reset' in text and len(parts) >= 3:
                        # Сбросить статус номера
                        phone = parts[2]
                        success = bot.reset_number_status(phone)
                        
                        if success:
                            vk.messages.send(
                                user_id=user_id,
                                message=f"✅ Статус номера {phone} сброшен",
                                random_id=0
                            )
                        else:
                            vk.messages.send(
                                user_id=user_id,
                                message=f"❌ Номер {phone} не найден",
                                random_id=0
                            )
                    
                    elif 'help' in text:
                        # Помощь для админа
                        response = (
                            "👑 **АДМИН КОМАНДЫ:**\n\n"
                            "📊 **Статистика:**\n"
                            "• /admin stats - общая статистика\n"
                            "• /admin reports [N] - последние N отчетов (по умолчанию 15)\n"
                            "• /admin managers - топ менеджеров\n"
                            "• /admin numbers [статус] - номера по статусу (new, called, callback)\n\n"
                            "🛠 **Управление:**\n"
                            "• /admin add <номер> <компания> <контакт> - добавить номер\n"
                            "• /admin reset <номер> - сбросить статус номера\n"
                            "• /admin export - экспорт всех данных (в разработке)\n\n"
                            "💡 **Примеры:**\n"
                            "/admin add +79991112233 ООО_Ромашка Иван\n"
                            "/admin reset +79991112233\n"
                            "/admin reports 10\n"
                            "/admin numbers called"
                        )
                        
                        vk.messages.send(user_id=user_id, message=response, random_id=0)
                
                # Обработка обычных сообщений
                elif text and not text.startswith('/'):
                    response = (
                        "Я бот для телемаркетинга! 🏢\n\n"
                        "Напишите 'начать' для старта работы или 'помощь' для списка команд."
                    )
                    
                    if is_admin(user_id):
                        response += "\n\nВы администратор! Напишите '/admin' для панели управления."
                    
                    vk.messages.send(user_id=user_id, message=response, random_id=0)
    
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}", exc_info=True)

if __name__ == '__main__':
    main()

