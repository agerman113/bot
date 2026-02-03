import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import sqlite3
import os
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение данных из переменных окружения
GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
GROUP_ID = os.getenv('VK_GROUP_ID')

# Настройка Google Sheets (если есть)
GOOGLE_SHEET_ID = os.getenv('GOOGLE_SHEET_ID', '')
GOOGLE_CREDS_JSON = os.getenv('GOOGLE_CREDS_JSON', '')

class TelemarketingBot:
    def __init__(self):
        self.db = sqlite3.connect('telemarketing.db', check_same_thread=False)
        self.init_database()
        self.init_google_sheets()
        
        # Тестовая база из 3 номеров
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
                status TEXT DEFAULT 'new', -- new, called, callback, invalid
                manager_id INTEGER,
                call_result TEXT,
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
                calls_made INTEGER DEFAULT 0,
                successful_calls INTEGER DEFAULT 0,
                last_active TIMESTAMP
            )
        ''')
        
        self.db.commit()
        logger.info("База данных инициализирована")
    
    def init_google_sheets(self):
        """Инициализация Google Sheets"""
        self.sheet = None
        if GOOGLE_SHEET_ID and GOOGLE_CREDS_JSON:
            try:
                # Сохраняем JSON во временный файл
                creds_dict = json.loads(GOOGLE_CREDS_JSON)
                with open('service_account.json', 'w') as f:
                    json.dump(creds_dict, f)
                
                # Авторизация
                scope = ['https://spreadsheets.google.com/feeds',
                        'https://www.googleapis.com/auth/drive']
                creds = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
                client = gspread.authorize(creds)
                
                # Открываем таблицу
                self.sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1
                
                # Создаем заголовки, если лист пустой
                if not self.sheet.get_all_values():
                    self.sheet.append_row([
                        'Дата и время', 'ID менеджера', 'Телефон', 
                        'Компания', 'Контакт', 'Результат', 'Комментарий'
                    ])
                
                logger.info("Google Sheets подключен")
            except Exception as e:
                logger.error(f"Ошибка подключения к Google Sheets: {e}")
        else:
            logger.warning("Google Sheets не настроен. Отчеты будут только в базе данных.")
    
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
    
    def get_next_number(self, manager_id):
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
                SET status = 'in_progress', manager_id = ?
                WHERE id = ?
            ''', (manager_id, number[0]))
            self.db.commit()
            
            # Получаем скрипт для звонка
            script = self.get_call_script()
            
            return {
                'id': number[0],
                'phone': number[1],
                'company': number[2],
                'contact': number[3],
                'description': number[4],
                'script': script
            }
        
        return None
    
    def get_call_script(self):
        """Получить скрипт для звонка"""
        return """
📞 СКРИПТ ДЛЯ ЗВОНКА:

1. Приветствие:
"Добрый день! Это [ваше имя] из сервиса удаленного телемаркетинга. Я по поводу развития вашего бизнеса."

2. Уточнение:
"Правильно ли я понимаю, что вы [должность] в компании [название компании]?"

3. Предложение:
"Мы помогаем компаниям увеличивать продажи через удаленных специалистов. 
Можем выделить вам подготовленного менеджера по цене от 500 руб/час."

4. Возражения:
"Понимаю, что это ново. Давайте проведем тестовый день - 2 часа работы за наш счет.
Если понравится - продолжим, если нет - просто поблагодарите."

5. Завершение:
"Когда вам удобно провести короткую 10-минутную встречу для деталей?"
"""
    
    def save_report(self, manager_id, number_id, result, comment=""):
        """Сохранить отчет о звонке"""
        cursor = self.db.cursor()
        
        # Получаем информацию о номере
        cursor.execute('''
            SELECT phone, company, contact_name 
            FROM phone_numbers WHERE id = ?
        ''', (number_id,))
        
        number_info = cursor.fetchone()
        
        if not number_info:
            return "Ошибка: номер не найден"
        
        phone, company, contact = number_info
        
        # Обновляем статус номера
        cursor.execute('''
            UPDATE phone_numbers 
            SET status = ?, call_result = ?, call_time = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (result, comment, number_id))
        
        # Обновляем статистику менеджера
        cursor.execute('''
            INSERT OR REPLACE INTO managers 
            (user_id, calls_made, successful_calls, last_active)
            VALUES (?, 
                COALESCE((SELECT calls_made FROM managers WHERE user_id = ?), 0) + 1,
                COALESCE((SELECT successful_calls FROM managers WHERE user_id = ?), 0) + ?,
                CURRENT_TIMESTAMP
            )
        ''', (manager_id, manager_id, manager_id, 1 if 'успешно' in result.lower() else 0))
        
        self.db.commit()
        
        # Отправляем в Google Sheets
        self.save_to_google_sheets(
            manager_id, phone, company, contact, result, comment
        )
        
        return "Отчет сохранен!"
    
    def save_to_google_sheets(self, manager_id, phone, company, contact, result, comment):
        """Сохранить отчет в Google Sheets"""
        if not self.sheet:
            return
        
        try:
            self.sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                manager_id,
                phone,
                company,
                contact,
                result,
                comment
            ])
            logger.info(f"Отчет сохранен в Google Sheets")
        except Exception as e:
            logger.error(f"Ошибка сохранения в Google Sheets: {e}")
    
    def get_manager_stats(self, manager_id):
        """Получить статистику менеджера"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT calls_made, successful_calls 
            FROM managers WHERE user_id = ?
        ''', (manager_id,))
        
        stats = cursor.fetchone()
        
        if stats:
            calls_made, successful = stats
            success_rate = (successful / calls_made * 100) if calls_made > 0 else 0
            
            return f"""
📊 Ваша статистика:
━━━━━━━━━━━━━━━━━
Всего звонков: {calls_made}
✅ Успешных: {successful}
📈 Конверсия: {success_rate:.1f}%
━━━━━━━━━━━━━━━━━
Ваш ID: {manager_id}
"""
        else:
            return "У вас еще нет статистики. Сделайте первый звонок!"
    
    def get_all_reports(self):
        """Получить все отчеты (для админа)"""
        cursor = self.db.cursor()
        
        cursor.execute('''
            SELECT p.phone, p.company, p.contact_name, 
                   p.call_result, p.call_time, m.user_id
            FROM phone_numbers p
            LEFT JOIN managers m ON p.manager_id = m.user_id
            WHERE p.status != 'new'
            ORDER BY p.call_time DESC
        ''')
        
        return cursor.fetchall()

# Инициализация бота
bot = TelemarketingBot()

def main():
    if not GROUP_TOKEN or not GROUP_ID:
        logger.error("Не установлены переменные окружения VK_GROUP_TOKEN и VK_GROUP_ID!")
        return
    
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
                
                # Команда: начало работы
                if text in ['начать', 'старт', 'работа', 'start']:
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_button('📞 Получить номер', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('📊 Моя статистика', color=VkKeyboardColor.PRIMARY)
                    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
                    
                    response = (
                        "🏢 Добро пожаловать в систему телемаркетинга!\n\n"
                        "Я помогу вам начать зарабатывать на удаленных звонках.\n\n"
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
                    number_data = bot.get_next_number(user_id)
                    
                    if number_data:
                        keyboard = VkKeyboard(one_time=False)
                        keyboard.add_button('✅ Успешный звонок', color=VkKeyboardColor.POSITIVE)
                        keyboard.add_button('📅 Перезвонить', color=VkKeyboardColor.PRIMARY)
                        keyboard.add_line()
                        keyboard.add_button('❌ Отказ', color=VkKeyboardColor.NEGATIVE)
                        keyboard.add_button('🚫 Неверный номер', color=VkKeyboardColor.SECONDARY)
                        
                        response = (
                            f"📞 **НОМЕР ДЛЯ ЗВОНКА:**\n"
                            f"━━━━━━━━━━━━━━━━━\n"
                            f"🏢 Компания: {number_data['company']}\n"
                            f"👤 Контакт: {number_data['contact']}\n"
                            f"📱 Телефон: {number_data['phone']}\n"
                            f"📝 Должность: {number_data['description']}\n"
                            f"━━━━━━━━━━━━━━━━━\n\n"
                            f"{number_data['script']}\n\n"
                            f"**После звонка нажмите одну из кнопок ниже:**"
                        )
                    else:
                        response = "😔 На данный момент нет доступных номеров.\nПопробуйте позже или напишите админу."
                        keyboard = None
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=keyboard.get_keyboard() if keyboard else None,
                        random_id=0
                    )
                
                # Команда: отчет о звонке
                elif any(cmd in text for cmd in ['успешный', 'перезвонить', 'отказ', 'неверный']):
                    # Получаем последний выданный номер
                    cursor = bot.db.cursor()
                    cursor.execute('''
                        SELECT id FROM phone_numbers 
                        WHERE manager_id = ? AND status = 'in_progress'
                        ORDER BY id DESC LIMIT 1
                    ''', (user_id,))
                    
                    last_number = cursor.fetchone()
                    
                    if last_number:
                        number_id = last_number[0]
                        
                        if 'успешный' in text:
                            result = 'success'
                            comment = "Клиент заинтересован, договорились о встрече"
                        elif 'перезвонить' in text:
                            result = 'callback'
                            comment = "Клиент занят, нужно перезвонить позже"
                        elif 'отказ' in text:
                            result = 'rejected'
                            comment = "Клиент не заинтересован"
                        else:
                            result = 'invalid'
                            comment = "Некорректный номер/неверные данные"
                        
                        # Сохраняем отчет
                        report_result = bot.save_report(user_id, number_id, result, comment)
                        
                        # Показываем статистику
                        stats = bot.get_manager_stats(user_id)
                        
                        keyboard = VkKeyboard(one_time=False)
                        keyboard.add_button('📞 Следующий номер', color=VkKeyboardColor.POSITIVE)
                        keyboard.add_button('📊 Моя статистика', color=VkKeyboardColor.PRIMARY)
                        
                        response = (
                            f"✅ {report_result}\n\n"
                            f"{stats}\n\n"
                            f"Хотите получить следующий номер?"
                        )
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            keyboard=keyboard.get_keyboard(),
                            random_id=0
                        )
                    else:
                        response = "Не найден активный номер для отчета.\nПолучите новый номер через меню."
                        vk.messages.send(user_id=user_id, message=response, random_id=0)
                
                # Команда: статистика
                elif 'статистика' in text or 'стата' in text:
                    stats = bot.get_manager_stats(user_id)
                    vk.messages.send(user_id=user_id, message=stats, random_id=0)
                
                # Команда: помощь
                elif 'помощь' in text or 'команды' in text:
                    response = (
                        "❓ **КОМАНДЫ БОТА:**\n\n"
                        "📞 **Получить номер** - получить номер для звонка\n"
                        "📊 **Моя статистика** - ваши результаты\n"
                        "❓ **Помощь** - это сообщение\n\n"
                        "**После звонка:**\n"
                        "✅ Успешный звонок - клиент заинтересован\n"
                        "📅 Перезвонить - клиент занят\n"
                        "❌ Отказ - клиент отказался\n"
                        "🚫 Неверный номер - некорректные данные\n\n"
                        "💰 **Оплата:** 50 руб за каждый успешный контакт\n"
                        "Выплаты по понедельникам на карту/кошелек."
                    )
                    vk.messages.send(user_id=user_id, message=response, random_id=0)
                
                # Админ команды (для вас)
                elif text.startswith('/admin'):
                    # Ваш ID ВК для проверки прав
                    admin_ids = [123456789]  # Замените на ваш ID ВК
                    
                    if user_id in admin_ids:
                        if 'отчеты' in text:
                            reports = bot.get_all_reports()
                            
                            if reports:
                                report_text = "📋 **ВСЕ ОТЧЕТЫ:**\n\n"
                                for i, (phone, company, contact, result, time, mgr_id) in enumerate(reports[:10], 1):
                                    report_text += f"{i}. 📞 {phone}\n   🏢 {company}\n   👤 {contact}\n   ✅ {result}\n   ⏰ {time}\n   👨‍💼 ID: {mgr_id}\n\n"
                            else:
                                report_text = "Пока нет отчетов."
                            
                            vk.messages.send(user_id=user_id, message=report_text, random_id=0)
                        elif 'база' in text:
                            cursor = bot.db.cursor()
                            cursor.execute('SELECT COUNT(*) FROM phone_numbers')
                            count = cursor.fetchone()[0]
                            
                            cursor.execute('SELECT COUNT(*) FROM phone_numbers WHERE status != "new"')
                            called = cursor.fetchone()[0]
                            
                            response = (
                                f"📊 **СТАТИСТИКА БАЗЫ:**\n\n"
                                f"Всего номеров: {count}\n"
                                f"Прозвонено: {called}\n"
                                f"Осталось: {count - called}\n\n"
                                f"Google Sheets: {'подключен' if bot.sheet else 'не подключен'}"
                            )
                            vk.messages.send(user_id=user_id, message=response, random_id=0)
    
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}")

if __name__ == '__main__':
    main()
