import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
import logging
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение данных из переменных окружения
GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
GROUP_ID = os.getenv('VK_GROUP_ID')

# Хранилище состояния пользователей (вместо БД для теста)
user_states = {}
user_projects = {}

# Данные из вашей таблицы (упрощенный вариант)
PARTNER_PROGRAMS = {
    "ai-up": {
        "name": "AI-Up (Перехватчик заявок)",
        "description": "Сервис перехвата заявок с сайтов",
        "url": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
        "has_leads": True,
        "steps": [
            "1. Зарегистрируйтесь по ссылке",
            "2. Подключите свой сайт или сайт клиента",
            "3. Настройте фильтры для сбора заявок",
            "4. Получайте уведомления о новых лидах"
        ]
    },
    "shikari": {
        "name": "Shikari (Сервис упоминаний)",
        "description": "Поиск упоминаний в соцсетях и форумах",
        "url": "https://shikari.do",
        "has_leads": True,
        "steps": [
            "1. Зарегистрируйтесь на сайте",
            "2. Настройте ключевые слова для мониторинга",
            "3. Получайте уведомления о релевантных обсуждениях",
            "4. Предлагайте свои услуги в комментариях"
        ]
    },
    "kwork": {
        "name": "Kwork (Биржа фриланса)",
        "description": "Площадка для продажи услуг",
        "url": "https://kwork.ru",
        "has_leads": True,
        "steps": [
            "1. Создайте аккаунт фрилансера",
            "2. Разместите свои услуги (кворки)",
            "3. Откликайтесь на проекты заказчиков",
            "4. Получайте заказы и отзывы"
        ]
    }
}

# Готовые связки из таблицы
BUNDLES = {
    "shikari_kwork": {
        "name": "Shikari + Kwork (Таргетинг)",
        "description": "Находим заказы на Shikari, выполняем через Kwork",
        "steps": [
            {
                "name": "Этап 1: Поиск клиентов",
                "url": "https://shikari.do/category/internet-marketing?page=1",
                "instruction": "Ищите запросы на таргетологов"
            },
            {
                "name": "Этап 2: Предложение услуг",
                "url": "https://kwork.ru/search?query=таргетолог",
                "instruction": "Предлагайте свои услуги через Kwork"
            }
        ]
    },
    "shikari_aiup": {
        "name": "Shikari + AI-Up (Перехват заявок)",
        "description": "Находим клиентов на Shikari, подключаем AI-Up",
        "steps": [
            {
                "name": "Этап 1: Поиск маркетологов",
                "url": "https://shikari.do/category/internet-marketing?page=1",
                "instruction": "Находите обсуждения про маркетинг"
            },
            {
                "name": "Этап 2: Внедрение AI-Up",
                "url": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "instruction": "Предлагайте сервис перехвата заявок"
            }
        ]
    }
}

def get_main_keyboard():
    """Клавиатура главного меню"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('📊 Партнерские программы', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🚀 Готовые связки', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('📋 Мои проекты', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('❓ Помощь', color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()

def get_programs_keyboard():
    """Клавиатура выбора партнерских программ"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🤖 AI-Up', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎯 Shikari', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('💼 Kwork', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('👨‍🏫 Репетиторы', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def get_bundles_keyboard():
    """Клавиатура выбора связок"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🎯 Таргетинг (Shikari+Kwork)', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🤖 Перехват заявок', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('👨‍🏫 Онлайн-репетиторы', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def get_step_keyboard(step_num, total_steps, bundle_id=None):
    """Клавиатура для пошагового прохождения"""
    keyboard = VkKeyboard(one_time=False)
    
    if step_num < total_steps:
        keyboard.add_button('✅ Шаг выполнен', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('➡️ Следующий шаг', color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button('🏁 Завершить проект', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    if bundle_id:
        keyboard.add_button('📋 Все шаги', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def main():
    if not GROUP_TOKEN or not GROUP_ID:
        logger.error("Не установлены переменные окружения!")
        return
    
    try:
        vk_session = vk_api.VkApi(token=GROUP_TOKEN)
        vk = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, GROUP_ID)
        
        logger.info(f"Бот запущен для группы ID: {GROUP_ID}")
        
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                message = event.obj.message
                user_id = message['from_id']
                text = message['text'].lower() if 'text' in message else ''
                
                # Обработка нажатий кнопок
                if 'payload' in message and message['payload']:
                    try:
                        payload = json.loads(message['payload'])
                        command = payload.get('command', '')
                    except:
                        command = ''
                else:
                    command = text
                
                logger.info(f"Сообщение от {user_id}: {text}")
                
                # Инициализация состояния пользователя
                if user_id not in user_states:
                    user_states[user_id] = 'main'
                    user_projects[user_id] = {}
                
                current_state = user_states[user_id]
                
                # Обработка команд
                if command in ['начать', 'привет', 'start', 'меню']:
                    response = (
                        "👋 Привет! Я бот для удаленной работы и телемаркетинга!\n"
                        "Я помогу тебе запустить проекты через партнерские программы.\n\n"
                        "Выбери действие:"
                    )
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_main_keyboard(),
                        random_id=0
                    )
                    user_states[user_id] = 'main'
                
                elif command == '📊 партнерские программы':
                    response = (
                        "📊 **Доступные партнерские программы:**\n\n"
                        "🤖 **AI-Up** - перехват заявок с сайтов\n"
                        "🎯 **Shikari** - поиск упоминаний в сети\n"
                        "💼 **Kwork** - биржа фриланса\n"
                        "👨‍🏫 **Репетиторы** - онлайн-обучение\n\n"
                        "Выбери программу для получения пошаговой инструкции:"
                    )
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_programs_keyboard(),
                        random_id=0
                    )
                    user_states[user_id] = 'programs'
                
                elif command == '🚀 готовые связки':
                    response = (
                        "🚀 **Готовые бизнес-связки:**\n\n"
                        "1. **🎯 Таргетинг** - Shikari + Kwork\n"
                        "   • Находим клиентов на Shikari\n"
                        "   • Выполняем заказы через Kwork\n\n"
                        "2. **🤖 Перехват заявок** - Shikari + AI-Up\n"
                        "   • Ищем маркетологов на Shikari\n"
                        "   • Предлагаем сервис AI-Up\n\n"
                        "Выбери связку для запуска:"
                    )
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                    user_states[user_id] = 'bundles'
                
                elif command == '📋 мои проекты':
                    if user_id in user_projects and user_projects[user_id]:
                        projects_text = "📋 **Ваши активные проекты:**\n\n"
                        for project_name, data in user_projects[user_id].items():
                            progress = data.get('progress', 0)
                            total = data.get('total_steps', 1)
                            projects_text += f"• {project_name}: {progress}/{total} шагов\n"
                    else:
                        projects_text = "У вас пока нет активных проектов.\nВыберите партнерскую программу или связку в меню."
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=projects_text,
                        keyboard=get_main_keyboard(),
                        random_id=0
                    )
                
                elif command == '❓ помощь':
                    response = (
                        "❓ **Как пользоваться ботом:**\n\n"
                        "1. Выберите **Партнерские программы** - отдельные сервисы\n"
                        "2. Выберите **Готовые связки** - пошаговые бизнес-цепочки\n"
                        "3. Проходите шаги по инструкции\n"
                        "4. Используйте реферальные ссылки для регистрации\n"
                        "5. Отслеживайте прогресс в **Мои проекты**\n\n"
                        "Все ссылки партнерские - вы поддерживаете разработчика!"
                    )
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_main_keyboard(),
                        random_id=0
                    )
                
                # Обработка выбора партнерских программ
                elif command in ['🤖 ai-up', 'ai-up']:
                    program = PARTNER_PROGRAMS['ai-up']
                    response = (
                        f"🤖 **{program['name']}**\n\n"
                        f"{program['description']}\n\n"
                        f"🔗 Реферальная ссылка:\n{program['url']}\n\n"
                        f"📋 **Пошаговая инструкция:**\n"
                        + "\n".join(program['steps']) + "\n\n"
                        f"Нажми '✅ Шаг выполнен' после каждого этапа."
                    )
                    
                    # Сохраняем проект пользователя
                    if 'ai-up' not in user_projects[user_id]:
                        user_projects[user_id]['ai-up'] = {
                            'current_step': 1,
                            'total_steps': len(program['steps']),
                            'progress': 0
                        }
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_step_keyboard(1, len(program['steps'])),
                        random_id=0
                    )
                    user_states[user_id] = 'program_aiup'
                
                elif command in ['🎯 shikari', 'shikari']:
                    program = PARTNER_PROGRAMS['shikari']
                    response = (
                        f"🎯 **{program['name']}**\n\n"
                        f"{program['description']}\n\n"
                        f"🔗 Ссылка: {program['url']}\n\n"
                        f"📋 **Пошаговая инструкция:**\n"
                        + "\n".join(program['steps'])
                    )
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_step_keyboard(1, len(program['steps'])),
                        random_id=0
                    )
                    user_states[user_id] = 'program_shikari'
                
                # Обработка выбора связок
                elif 'таргетинг' in command or 'shikari+kwork' in command:
                    bundle = BUNDLES['shikari_kwork']
                    response = (
                        f"🎯 **{bundle['name']}**\n\n"
                        f"{bundle['description']}\n\n"
                        f"🔗 **Этап 1: {bundle['steps'][0]['name']}**\n"
                        f"Ссылка: {bundle['steps'][0]['url']}\n"
                        f"Инструкция: {bundle['steps'][0]['instruction']}"
                    )
                    
                    # Сохраняем проект связки
                    user_projects[user_id]['shikari_kwork'] = {
                        'current_step': 1,
                        'total_steps': len(bundle['steps']),
                        'progress': 0
                    }
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_step_keyboard(1, len(bundle['steps']), 'shikari_kwork'),
                        random_id=0
                    )
                    user_states[user_id] = 'bundle_shikari_kwork'
                
                # Обработка пошаговых действий
                elif '➡️ следующий шаг' in command.lower():
                    if user_states[user_id] == 'bundle_shikari_kwork':
                        bundle = BUNDLES['shikari_kwork']
                        if user_projects[user_id]['shikari_kwork']['current_step'] < len(bundle['steps']):
                            next_step = user_projects[user_id]['shikari_kwork']['current_step']
                            step_data = bundle['steps'][next_step]
                            
                            response = (
                                f"🔗 **Этап {next_step + 1}: {step_data['name']}**\n\n"
                                f"Ссылка: {step_data['url']}\n"
                                f"Инструкция: {step_data['instruction']}"
                            )
                            
                            user_projects[user_id]['shikari_kwork']['current_step'] += 1
                            user_projects[user_id]['shikari_kwork']['progress'] += 1
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                keyboard=get_step_keyboard(
                                    next_step + 1, 
                                    len(bundle['steps']), 
                                    'shikari_kwork'
                                ),
                                random_id=0
                            )
                
                elif '◀️ назад' in command.lower():
                    response = "Главное меню:"
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_main_keyboard(),
                        random_id=0
                    )
                    user_states[user_id] = 'main'
                
                # Обработка обычных сообщений
                elif text:
                    response = (
                        "Выберите действие через меню кнопок 👇\n"
                        "Или напишите 'меню' для показа клавиатуры."
                    )
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_main_keyboard(),
                        random_id=0
                    )
    
    except Exception as e:
        logger.error(f"Ошибка: {e}")

if __name__ == '__main__':
    main()
