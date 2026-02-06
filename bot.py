import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
import json
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение данных из переменных окружения
GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
GROUP_ID = os.getenv('VK_GROUP_ID')

# Хранилище прогресса пользователей (в продакшене - БД)
user_progress = {}

# ==================== ДАННЫЕ ИЗ ВАШЕГО EXCEL ====================

PARTNER_PROGRAMS = {
    "shikari": {
        "name": "🎯 Сервис поиска клиентов",
        "description": "Находите людей, которые прямо сейчас ищут услуги",
        "short_desc": "Поиск живых заявок",
        "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
        "has_leads": True,
        "reward": "До 15% с каждой сделки клиента"
    },
    "ai_up": {
        "name": "🤖 Перехватчик заявок",
        "description": "Автоматический сбор заявок с сайтов конкурентов",
        "short_desc": "Автоподбор клиентов",
        "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
        "has_leads": True,
        "reward": "Фиксированные выплаты за лиды"
    },
    "kwork": {
        "name": "💼 Биржа фриланса",
        "description": "Площадка для продажи услуг и поиска исполнителей",
        "short_desc": "Биржа услуг",
        "ref_link": "https://kwork.ru/ref/13103246",
        "has_leads": True,
        "reward": "Процент с каждой сделки"
    },
    "foxford": {
        "name": "👨‍🏫 Онлайн-школа",
        "description": "Образовательная платформа с партнерской программой",
        "short_desc": "Обучение и репетиторство",
        "ref_link": "https://partner.foxford.ru/webmaster",
        "has_leads": False,
        "reward": "До 30% с каждой продажи курса"
    },
    "saleads": {
        "name": "📈 Партнерская сеть",
        "description": "Много офферов с автоматическими выплатами",
        "short_desc": "Разные ниши",
        "ref_link": "https://saleads.pro/register/75a0d2d0-4d15-11ed-b6cb-099fc6fcedfb",
        "has_leads": False,
        "reward": "Разные ставки, есть CPA"
    }
}

# Готовые связки из Excel
BUNDLES = {
    1: {
        "id": "tutors_bundle",
        "name": "👨‍🏫 Репетиторство",
        "emoji": "👨‍🏫",
        "difficulty": "★☆☆",
        "time": "10-15 мин",
        "potential": "500-2000 руб/день",
        "description": "Помогаем находить учеников для репетиторов",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в основном сервисе",
                "description": "Зарегистрируйтесь в сервисе поиска клиентов по моей ссылке. Это ваш инструмент для старта.",
                "action": "Нажмите кнопку ниже для перехода и регистрации",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "hint": "После регистрации вернитесь в бота"
            },
            {
                "number": 2,
                "title": "Ищем нуждающихся в репетиторе",
                "description": "В разделе 'Обучение' ищите сообщения типа 'Нужен репетитор по математике'",
                "action": "Найдите 3 свежих запроса",
                "ref_link": None,
                "hint": "Люди сами пишут что им нужно - ваша задача просто откликнуться"
            },
            {
                "number": 3,
                "title": "Пишем предложение",
                "description": "Напишите человеку: 'Привет! Вижу вы ищете репетитора. Я могу порекомендовать проверенную платформу, где много специалистов с отзывами. Бесплатно помогу подобрать под ваш запрос.'",
                "action": "Скопируйте и адаптируйте этот текст",
                "ref_link": None,
                "hint": "Говорите как друг, а не как продавец"
            },
            {
                "number": 4,
                "title": "Даем решение",
                "description": "Отправьте человеку ссылку на образовательную платформу",
                "action": "Используйте партнерскую ссылку",
                "ref_link": "https://partner.foxford.ru/webmaster",
                "hint": "После перехода по ссылке - напишите мне 'готово'"
            },
            {
                "number": 5,
                "title": "Закрываем сделку",
                "description": "Уточните, нашел ли человек репетитора. Если да - вы заработали! Если нет - предложите помощь в поиске.",
                "action": "Напишите финальное сообщение",
                "ref_link": None,
                "hint": "Ваша цель - помочь, а не просто отправить ссылку"
            }
        ],
        "results": [
            "✅ Вы получаете 20-30% с первой оплаты ученика",
            "✅ Репетитор получает клиента",
            "✅ Ученик находит учителя",
            "✅ Все довольны - это честная модель"
        ]
    },
    
    2: {
        "id": "targetology_bundle",
        "name": "🎯 Таргетологи и маркетологи",
        "emoji": "🎯",
        "difficulty": "★★☆",
        "time": "20-30 мин",
        "potential": "1000-5000 руб/день",
        "description": "Связываем бизнесы с маркетологами через умные сервисы",
        "steps": [
            {
                "number": 1,
                "title": "Двойная регистрация",
                "description": "Зарегистрируйтесь в двух сервисах (поиск + автоматизация)",
                "action": "Используйте обе ссылки ниже",
                "ref_links": [
                    {"name": "Поиск клиентов", "url": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1"},
                    {"name": "Автоматизация", "url": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19"}
                ],
                "hint": "Это ваш арсенал на ближайшие 2 часа"
            },
            {
                "number": 2,
                "title": "Ищем бизнесы, которым нужна помощь",
                "description": "В разделе 'Интернет-маркетинг' ищите: 'Нужен таргетолог', 'Ищу SMM-специалиста'",
                "action": "Найдите 5 активных запросов",
                "ref_link": None,
                "hint": "Бизнесы готовы платить за клиентов - вы им нужны"
            },
            {
                "number": 3,
                "title": "Предлагаем решение проблемы",
                "description": "Напишите: 'Здравствуйте! Вижу вы ищете специалиста по привлечению клиентов. А пробовали автоматический сбор заявок? Система сама находит тех, кто ищет ваши услуги прямо сейчас.'",
                "action": "Используйте этот подход",
                "ref_link": None,
                "hint": "Продавайте решение проблемы, а не услугу"
            },
            {
                "number": 4,
                "title": "Демонстрируем инструмент",
                "description": "Покажите скриншоты/примеры работы сервиса перехвата заявок",
                "action": "Отправьте ссылку на сервис",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "hint": "Говорите на языке выгод для бизнеса: 'экономия времени', 'постоянный поток заявок'"
            }
        ],
        "results": [
            "✅ Вы получаете выплаты за каждого подключенного клиента",
            "✅ Бизнес получает систему привлечения заявок",
            "✅ Маркетологи получают инструмент для работы",
            "✅ Вы становитесь ценным посредником"
        ]
    }
}

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard():
    """Главное меню"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🚀 Начать зарабатывать', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('📊 Партнерские программы', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎯 Готовые связки', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('📝 Оформить ИП', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('👨‍💼 Связь с автором', color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()

def get_bundles_keyboard():
    """Выбор связки"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('👨‍🏫 Репетиторство', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🎯 Таргетологи', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('📧 Email-рассылки', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('👷 Сантехники', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('🏗️ Строительный бизнес', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🎓 Помощь студентам', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def get_bundle_steps_keyboard(bundle_id, step_number, total_steps):
    """Шаги в связке"""
    keyboard = VkKeyboard(one_time=False)
    
    if step_number < total_steps:
        keyboard.add_button('✅ Шаг выполнен', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('➡️ Далее', color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button('🎉 Завершить связку', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('📋 Все шаги', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('◀️ К связкам', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def get_programs_keyboard():
    """Партнерские программы"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🎯 Shikari', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🤖 AI-Up', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('💼 Kwork', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('👨‍🏫 Foxford', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('📈 Saleads', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📧 Notisend', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

# ==================== ТЕКСТОВЫЕ ШАБЛОНЫ ====================

WELCOME_MESSAGE = """🌟 *ДОБРО ПОЖАЛОВАТЬ В "ПАРТНЕРСКИЙ ПУТЬ"* 🌟

Я — твой цифровой наставник в мире *партнерских программ и удаленного заработка*.

✨ *ЧТО Я ДЕЛАЮ:*
• Превращаю скучные "партнерки" в увлекательные квесты
• Даю *готовые связки* — бери и делай
• Показываю, как находить клиентов там, где их ищут
• Помогаю зарабатывать *от 500 до 5000 руб в день* с нуля

🎯 *ПРИНЦИП РАБОТЫ:*
1. Ты находишь человека, которому что-то нужно
2. Предлагаешь ему решение через партнерский сервис
3. Получаешь процент, когда он платит
4. Все довольны — ты помог и заработал

🚀 *СЕЙЧАС ТЫ МОЖЕШЬ:*
• Начать с простой связки "Репетиторство" (10-15 минут)
• Изучить все партнерские программы
• Оформить ИП для серьезного заработка
• Связаться с автором для расширения возможностей

*Выбирай действие ниже ⬇️*"""

ABOUT_BOT = """🤖 *О БОТЕ "ПАРТНЕРСКИЙ ПУТЬ"*

Это не просто бот — это *система заработка*, которую я создал на основе личного опыта в партнерских программах.

📊 *ЧТО ВНУТРИ:*
• *9 готовых связок* из реальной практики
• *15+ партнерских программ* с проверенными выплатами
• *Пошаговые инструкции* — от регистрации до первого заработка
• *Мотивационная система* — чтобы не бросить на полпути

🎨 *ФИЛОСОФИЯ:*
«Зарабатывать, помогая другим» — это не красивые слова. Когда ты находишь репетитора для школьника, маркетолога для бизнеса или сантехника для семьи — ты решаешь реальные проблемы и получаешь за это деньги.

⚡ *ПОЧЕМУ ЭТО РАБОТАЕТ:*
1. *Люди сами ищут услуги* (в соцсетях, на форумах)
2. *Ты становишься полезным посредником*
3. *Сервисы платят за приведенных клиентов*
4. *Ты зарабатываешь на ценности, которую создал*

💰 *СКОЛЬКО МОЖНО ЗАРАБОТАТЬ:*
• *Новичок:* 500-2000 руб/день (первые 2 недели)
• *Опытный:* 2000-5000 руб/день (через 1 месяц)
• *Профессионал:* 5000-20000 руб/день (системный подход)

*Готов начать? Выбирай связку ниже!* ⬇️"""

IP_REGISTRATION = """📝 *ОФОРМЛЕНИЕ ИП: ВАШ ПЕРВЫЙ ШАГ К СЕРЬЕЗНОМУ ЗАРАБОТКУ*

🎯 *ЗАЧЕМ ЭТО НУЖНО?*
Когда ты начинаешь зарабатывать от 30-50 тыс. руб/месяц на партнерках — пора оформлять *Индивидуального Предпринимателя*.

✨ *ПРЕИМУЩЕСТВА ИП:*
• ✅ *Легальный доход* — спишь спокойно
• ✅ *Налоговые льготы* — платишь минимум (6% от дохода)
• ✅ *Банковские переводы* — принимаешь оплату от юрлиц
• ✅ *Договоры с компаниями* — работаешь с крупными партнерами
• ✅ *Пенсионный стаж* — идет автоматически

⚠️ *БЕЗ ИП ТЫ:*
• Не можешь принимать оплату от многих партнерских программ
• Рискуешь блокировкой счетов при больших суммах
• Ограничиваешь свой рост

🚀 *КАК ОФОРМИТЬ:*
Я сотрудничаю с *проверенным онлайн-сервисом*, который:
• Оформляет ИП *за 1 день*
• Стоит *от 1990 руб* (дешевле, чем самому)
• Дает *консультацию по налогам*
• Помогает *открыть расчетный счет*

🔒 *ВАЖНО:* 
Я *не раскрываю название сервиса* до перехода по ссылке, чтобы:
1. Ты получил *мою партнерскую скидку*
2. Сервис знал, что ты *от меня*
3. Я мог *проконтролировать* процесс оформления

📌 *ЧТО ДЕЛАТЬ ДАЛЬШЕ:*
1. Нажми кнопку *«Перейти к оформлению»*
2. Заполни форму на сайте (5-7 минут)
3. Получи документы на email
4. Вернись в бота — я дам *дополнительный бонус*

*Готов стать официальным предпринимателем?* ⬇️"""

CONTACT_AUTHOR = """👨‍💼 *СВЯЗЬ С АВТОРОМ И ПОЛУЧЕНИЕ КОДА БОТА*

Привет! Меня зовут *[Твое имя]*, я создал этого бота и всю систему заработка.

🎯 *ЧЕМ Я МОГУ ПОМОЧЬ:*
• *Настроить этого бота* под твою нишу
• *Добавить твои партнерские программы*
• *Создать новые связки* на основе твоего опыта
• *Оптимизировать процесс* для максимальной конверсии

💻 *ПОЛНЫЙ КОД БОТА:*
Я выкладываю *полный исходный код* этого бота в *приватный репозиторий* для тех, кто:
1. Прошел *хотя бы одну связку до конца*
2. Оформил *ИП по моей ссылке*
3. Хочет *масштабировать систему* под себя

🚀 *ЧТО ТЫ ПОЛУЧИШЬ С КОДОМ:*
• *Полностью рабочий бот* на Python
• *Базу данных* для отслеживания прогресса
• *Систему админ-панели* для управления
• *Инструкцию по деплою* на хостинг
• *Поддержку* по настройке и адаптации

📞 *КАК СВЯЗАТЬСЯ:*
1. *Telegram:* @[твой_username]
2. *Email:* [твой@email.com]
3. *VK:* [ссылка на твою страницу]

💬 *ПРИ СООБЩЕНИИ УКАЖИ:*
• Какая связка тебе понравилась больше всего
• Сколько ты уже заработал через бота
• Что хочешь изменить/добавить

✨ *БОНУС:* 
Первым 10 обратившимся — *бесплатная консультация* по настройке их собственного бота!

*Жду твоего сообщения!* 🚀"""

# ==================== ОСНОВНОЙ КОД ====================

def main():
    if not GROUP_TOKEN or not GROUP_ID:
        logger.error("Не установлены переменные окружения!")
        return
    
    try:
        vk_session = vk_api.VkApi(token=GROUP_TOKEN)
        vk = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, GROUP_ID)
        
        logger.info(f"Бот 'Партнерский Путь' запущен!")
        
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                message = event.obj.message
                user_id = message['from_id']
                text = message['text'].lower() if 'text' in message else ''
                
                # Инициализация пользователя
                if user_id not in user_progress:
                    user_progress[user_id] = {
                        'current_bundle': None,
                        'current_step': 0,
                        'completed_bundles': [],
                        'total_earned': 0,
                        'registration_time': datetime.now()
                    }
                
                # Главное меню
                if text in ['начать', 'старт', 'start', 'меню', 'привет']:
                    vk.messages.send(
                        user_id=user_id,
                        message=WELCOME_MESSAGE,
                        keyboard=get_main_keyboard(),
                        random_id=0,
                        dont_parse_links=0
                    )
                
                # Кнопка "Начать зарабатывать"
                elif 'начать зарабатывать' in text or text == 'старт заработка':
                    response = (
                        "🎯 *ВЫБЕРИ СВОЙ ПУТЬ К ПЕРВОМУ ЗАРАБОТКУ:*\n\n"
                        "👨‍🏫 *РЕПЕТИТОРСТВО* (★☆☆)\n"
                        "• Время: 10-15 минут\n"
                        "• Потенциал: 500-2000 руб/день\n"
                        "• Идеально для новичков\n\n"
                        "🎯 *ТАРГЕТОЛОГИ* (★★☆)\n"
                        "• Время: 20-30 минут\n"
                        "• Потенциал: 1000-5000 руб/день\n"
                        "• Для тех, кто хочет больше\n\n"
                        "📧 *EMAIL-РАССЫЛКИ* (★★☆)\n"
                        "• Время: 25-40 минут\n"
                        "• Потенциал: 1500-6000 руб/день\n"
                        "• Работа с бизнесом\n\n"
                        "*Какую связку выбираешь?*"
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                
                # Партнерские программы
                elif 'партнерские программы' in text:
                    response = (
                        "📊 *ПАРТНЕРСКИЕ ПРОГРАММЫ* — твой арсенал\n\n"
                        "Каждая программа — это *инструмент* для решения проблем людей "
                        "и получения процента с их оплаты.\n\n"
                        "*Выбери программу для изучения:*"
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_programs_keyboard(),
                        random_id=0
                    )
                
                # Готовые связки
                elif 'готовые связки' in text:
                    response = (
                        "🎯 *ГОТОВЫЕ СВЯЗКИ* — твой план заработка\n\n"
                        "Связка = *пошаговый план* из нескольких партнерских программ.\n"
                        "Ты помогаешь человеку → получаешь процент с нескольких сервисов.\n\n"
                        "*Пример:*\n"
                        "1. Находишь того, кто ищет репетитора\n"
                        "2. Предлагаешь платформу с репетиторами (программа 1)\n"
                        "3. Если не нашел — предлагаешь курсы (программа 2)\n"
                        "4. Зарабатываешь с обеих программ!\n\n"
                        "*Выбери нишу:*"
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                
                # Оформить ИП
                elif 'оформить ип' in text or 'ип' in text:
                    vk.messages.send(
                        user_id=user_id,
                        message=IP_REGISTRATION,
                        random_id=0,
                        dont_parse_links=0
                    )
                    
                    # Кнопка для перехода по ссылке
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_button('🚀 Перейти к оформлению', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
                    
                    vk.messages.send(
                        user_id=user_id,
                        message="*Нажми кнопку ниже для перехода на сайт оформления:*",
                        keyboard=keyboard.get_keyboard(),
                        random_id=0
                    )
                
                # Переход по ИП ссылке (скрытая команда)
                elif 'перейти к оформлению' in text:
                    response = (
                        "🔗 *СЕКРЕТНАЯ ССЫЛКА ДЛЯ ТЕБЯ:*\n\n"
                        "https://saleads.pro/lk/webmaster/offer/fa873860-8047-11e8-ae6f-c5b371f9b8f9\n\n"
                        "*ИНСТРУКЦИЯ:*\n"
                        "1. Перейди по ссылке выше\n"
                        "2. Выбери 'Регистрация ИП'\n"
                        "3. Заполни форму (5-7 минут)\n"
                        "4. Оплати от 1990 руб\n"
                        "5. Получи документы на email\n\n"
                        "*ВОЗВРАЩАЙСЯ В БОТА ПОСЛЕ ОФОРМЛЕНИЯ!*\n"
                        "Я дам тебе *дополнительный бонус* и *доступ к коду бота*."
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        random_id=0
                    )
                
                # Связь с автором
                elif 'связь с автором' in text or 'автор' in text:
                    vk.messages.send(
                        user_id=user_id,
                        message=CONTACT_AUTHOR,
                        random_id=0,
                        dont_parse_links=0
                    )
                
                # Выбор связки: Репетиторство
                elif 'репетиторство' in text:
                    bundle = BUNDLES[1]
                    user_progress[user_id]['current_bundle'] = 1
                    user_progress[user_id]['current_step'] = 1
                    
                    response = (
                        f"{bundle['emoji']} *{bundle['name']}*\n"
                        f"──────────────────\n"
                        f"📊 Сложность: {bundle['difficulty']}\n"
                        f"⏱ Время: {bundle['time']}\n"
                        f"💰 Потенциал: {bundle['potential']}\n\n"
                        f"*{bundle['description']}*\n\n"
                        f"🎯 *КАК ЭТО РАБОТАЕТ:*\n"
                        "1. Люди в соцсетях ищут репетиторов\n"
                        "2. Ты находишь эти запросы\n"
                        "3. Предлагаешь платформу с проверенными репетиторами\n"
                        "4. Получаешь процент, когда ученик оплачивает уроки\n\n"
                        f"✨ *РЕЗУЛЬТАТ ДЛЯ ТЕБЯ:*\n"
                        + "\n".join(bundle['results']) + "\n\n"
                        f"*Готов начать? Первый шаг ниже!*"
                    )
                    
                    # Показываем первый шаг
                    step = bundle['steps'][0]
                    
                    step_response = (
                        f"🚀 *ШАГ {step['number']}: {step['title']}*\n"
                        f"──────────────────\n"
                        f"{step['description']}\n\n"
                        f"📌 *ТВОЕ ДЕЙСТВИЕ:*\n"
                        f"{step['action']}\n\n"
                        f"💡 *СОВЕТ:* {step['hint']}"
                    )
                    
                    # Клавиатура с ссылкой
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_button('🔗 Перейти к регистрации', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_line()
                    keyboard.add_button('✅ Шаг выполнен', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_button('➡️ Далее', color=VkKeyboardColor.PRIMARY)
                    keyboard.add_line()
                    keyboard.add_button('◀️ К связкам', color=VkKeyboardColor.NEGATIVE)
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        random_id=0
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=step_response,
                        keyboard=keyboard.get_keyboard(),
                        random_id=0
                    )
                
                # Переход по ссылке регистрации
                elif 'перейти к регистрации' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    if bundle_id:
                        bundle = BUNDLES[bundle_id]
                        step = bundle['steps'][0]
                        
                        if 'ref_links' in step:
                            response = "🔗 *ССЫЛКИ ДЛЯ РЕГИСТРАЦИИ:*\n\n"
                            for link in step['ref_links']:
                                response += f"• *{link['name']}:* {link['url']}\n"
                        else:
                            response = f"🔗 *ТВОЯ ПАРТНЕРСКАЯ ССЫЛКА:*\n{step['ref_link']}\n\n"
                        
                        response += "\n*ВОЗВРАЩАЙСЯ В БОТА ПОСЛЕ РЕГИСТРАЦИИ!*"
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            random_id=0
                        )
                
                # Обработка шагов в связке
                elif 'далее' in text or 'шаг выполнен' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    current_step = user_progress[user_id]['current_step']
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        
                        if current_step < len(bundle['steps']):
                            # Переход к следующему шагу
                            next_step = bundle['steps'][current_step]
                            user_progress[user_id]['current_step'] += 1
                            
                            response = (
                                f"✅ *Отлично! Переходим к шагу {next_step['number']}:*\n\n"
                                f"🎯 *{next_step['title']}*\n"
                                f"──────────────────\n"
                                f"{next_step['description']}\n\n"
                                f"📌 *ТВОЕ ДЕЙСТВИЕ:*\n"
                                f"{next_step['action']}\n\n"
                                f"💡 *СОВЕТ:* {next_step['hint']}"
                            )
                            
                            keyboard = get_bundle_steps_keyboard(
                                bundle_id, 
                                next_step['number'], 
                                len(bundle['steps'])
                            )
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                keyboard=keyboard,
                                random_id=0
                            )
                        else:
                            # Завершение связки
                            user_progress[user_id]['completed_bundles'].append(bundle_id)
                            user_progress[user_id]['total_earned'] += 500  # Пример
                            
                            response = (
                                f"🎉 *ПОЗДРАВЛЯЮ! ТЫ ЗАВЕРШИЛ СВЯЗКУ!*\n\n"
                                f"✨ *ЧТО ТЫ СДЕЛАЛ:*\n"
                                f"• Прошел {len(bundle['steps'])} шагов\n"
                                f"• Освоил новую нишу\n"
                                f"• Заработал первые 500 руб (в потенциале)\n\n"
                                f"💰 *ТВОЙ ПРОГРЕСС:*\n"
                                f"• Заработано: {user_progress[user_id]['total_earned']} руб\n"
                                f"• Связок завершено: {len(user_progress[user_id]['completed_bundles'])}\n\n"
                                f"🚀 *ЧТО ДАЛЬШЕ?*\n"
                                "1. Повтори связку 2-3 раза для закрепления\n"
                                "2. Выбери новую связку из меню\n"
                                "3. Оформи ИП для серьезного заработка\n"
                                "4. Свяжись со мной для получения кода бота"
                            )
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                keyboard=get_main_keyboard(),
                                random_id=0
                            )
                
                # Назад к связкам
                elif 'к связкам' in text:
                    user_progress[user_id]['current_bundle'] = None
                    user_progress[user_id]['current_step'] = 0
                    
                    vk.messages.send(
                        user_id=user_id,
                        message="Выбери новую связку для старта:",
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                
                # Назад в главное меню
                elif 'назад' in text:
                    vk.messages.send(
                        user_id=user_id,
                        message="Возвращаю в главное меню:",
                        keyboard=get_main_keyboard(),
                        random_id=0
                    )
                
                # Информация о партнерских программах
                elif text in ['shikari', 'ai-up', 'kwork', 'foxford', 'saleads']:
                    program_key = text.replace('-', '_')
                    if program_key in PARTNER_PROGRAMS:
                        program = PARTNER_PROGRAMS[program_key]
                        
                        response = (
                            f"{program['name']}\n"
                            f"──────────────────\n"
                            f"📝 *Описание:* {program['description']}\n\n"
                            f"💰 *Вознаграждение:* {program['reward']}\n\n"
                            f"🔗 *Партнерская ссылка:*\n"
                            f"{program['ref_link']}\n\n"
                            f"💡 *КАК ИСПОЛЬЗОВАТЬ:*\n"
                            "1. Регистрируйся по ссылке\n"
                            "2. Изучи личный кабинет\n"
                            "3. Используй в готовых связках\n"
                            "4. Получай выплаты за приведенных клиентов"
                        )
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            random_id=0
                        )
    
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}", exc_info=True)

if __name__ == '__main__':
    main()
