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

# Ваша ссылка на регистрацию ИП
IP_LINK = "https://my.saleads.pro/s/57bkq"

# Хранилище прогресса пользователей
user_progress = {}

# ==================== ДАННЫЕ ИЗ ТАБЛИЦЫ ====================

ADVANTAGES = [
    "✅ Сложная многоуровневая партнерская система",
    "✅ Без занудных обучений и вебинаров",
    "✅ Полностью бесплатно — мы заинтересованы в том, чтобы вы зарабатывали",
    "✅ Более 50 готовых связок, которые вы никогда не видели на YouTube",
    "✅ 3 источника горячих клиентов без рекламного бюджета",
    "✅ Сразу начинай в боте, даже без опыта",
    "✅ Полезно как для новичков, так и для опытных",
    "✅ Настрой систему один раз, и она будет работать годами"
]

IP_MESSAGE = f"""📝 *ОФОРМЛЕНИЕ ИП ДЛЯ СЕРЬЕЗНОГО ЗАРАБОТКА*

🎯 *ПОЧЕМУ ЭТО ВАЖНО:*
Когда твой доход превышает 30-50 тыс. рублей в месяц, 
оформление ИП становится необходимостью для легальной работы.

✨ *ПРЕИМУЩЕСТВА ИП:*
✅ Легальный доход — работаешь спокойно
✅ Налоговые льготы — всего 6% от дохода
✅ Прием платежей от юрлиц и компаний
✅ Договоры с партнерскими программами
✅ Пенсионный стаж — накапливается автоматически

⚠️ *БЕЗ ИП ТЫ:*
• Не можешь принимать выплаты от многих программ
• Рискуешь блокировкой счетов
• Ограничиваешь свой рост

🔗 *МОЯ ПАРТНЕРСКАЯ ССЫЛКА:*
Для оформления ИП я сотрудничаю с проверенным сервисом. 
Переходи по ссылке ниже, чтобы получить мою партнерскую скидку:

[Ссылка на регистрацию ИП]({IP_LINK})

📌 *ИНСТРУКЦИЯ:*
1. Перейди по ссылке выше
2. Выбери "Регистрация ИП"
3. Заполни форму (5-7 минут)
4. Оплати от 1990 рублей
5. Получи документы на email

💎 *БОНУС:*
После оформления ИП напиши мне "ИП готово" — 
я дам доступ к эксклюзивным материалам!"""

INFO_MESSAGE = """ℹ️ *ИНФОРМАЦИЯ О ПРОЕКТЕ И ПОДДЕРЖКА*

👨‍💼 *АВТОР ПРОЕКТА:*
• Имя: Андрей Герман
• Email для связи: agerman113@vk.com
• Специализация: партнерские программы, телемаркетинг, автоматизация

🤖 *О БОТЕ:*
Этот бот — часть комплексной системы заработка на партнерских программах. 
Здесь собраны 10 проверенных связок, которые приносят реальный доход.

📊 *ЧТО ВКЛЮЧЕНО:*
• 10 готовых связок с пошаговыми инструкциями
• Партнерские ссылки на все сервисы
• Мотивационная система прохождения
• Поддержка и консультации

🚀 *ВОЗМОЖНОСТИ ДЛЯ ТЕБЯ:*
1. Начать зарабатывать с первой связки уже сегодня
2. Масштабировать доход, добавляя новые связки
3. Получить код бота для создания своей системы
4. Стать партнером и получать процент с учеников

❓ *ЧАСТО ЗАДАВАЕМЫЕ ВОПРОСЫ:*

Q: Сколько нужно времени на одну связку?
A: От 15 до 60 минут в зависимости от сложности.

Q: Нужны ли вложения?
A: Нет, все сервисы регистрируются бесплатно.

Q: Когда приходят первые деньги?
A: От 1 до 7 дней, в зависимости от партнерской программы.

Q: Можно ли работать без ИП?
A: Да, но для доходов от 30к/мес ИП обязателен.

Q: Как получить код бота?
A: После прохождения 3-х связок и оформления ИП.

📞 *ТЕХНИЧЕСКАЯ ПОДДЕРЖКА:*
По всем вопросам пишите на: agerman113@vk.com
В теме письма укажите: "Вопрос по боту"

⚡ *НАЧНИТЕ ПРЯМО СЕЙЧАС — ВЫБЕРИТЕ СВЯЗКУ В МЕНЮ!*"""

# 10 связок из таблицы с сохранением структуры
BUNDLES = {
    1: {
        "id": "s_repetitory_f",
        "name": "S-репетиторы-F",
        "emoji": "👨‍🏫",
        "difficulty": "★☆☆",
        "time": "15-20 мин",
        "potential": "500-2000 руб",
        "description": "Находим учеников для репетиторов через Shikari + Foxford",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Зарегистрируйтесь в сервисе поиска клиентов Shikari по моей ссылке",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Поиск клиентов",
                "description": "Заходим в раздел 'Обучение, репетиторство, курсы' и находим запросы на репетиторов",
                "action": "Найдите 3 свежих запроса",
                "ref_link": None
            },
            {
                "number": 3,
                "title": "Написание предложения",
                "description": "Пишем потенциальному клиенту в разговорной форме, предлагая помощь в поиске репетитора",
                "action": "Создайте персонализированное сообщение",
                "ref_link": None
            },
            {
                "number": 4,
                "title": "Отправка реферальной ссылки",
                "description": "Отправляем свою реферальную ссылку на сервис Foxford с репетиторами",
                "action": "Используйте партнерскую ссылку",
                "ref_link": "https://partner.foxford.ru/webmaster",
                "ref_text": "Ссылка на регистрацию Foxford"
            },
            {
                "number": 5,
                "title": "Помощь в регистрации",
                "description": "Интересуемся у пользователя, получилось ли освоить сервис, помогаем завершить регистрацию",
                "action": "Напишите финальное сообщение с поддержкой",
                "ref_link": None
            }
        ]
    },
    
    2: {
        "id": "s_k_targetologi_k",
        "name": "S-K-таргетологи-K",
        "emoji": "🎯",
        "difficulty": "★★☆",
        "time": "25-35 мин",
        "potential": "1000-5000 руб",
        "description": "Находим таргетологов на Shikari и направляем на Kwork",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Регистрируемся в сервисе Shikari по ссылке",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Регистрация на Kwork",
                "description": "Регистрируемся на бирже фриланса Kwork",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://kwork.ru/ref/13103246",
                "ref_text": "Ссылка на регистрацию Kwork"
            },
            {
                "number": 3,
                "title": "Поиск таргетологов",
                "description": "Заходим в раздел 'Интернет-маркетинг' на Shikari, ищем запросы на таргетологов",
                "action": "Найдите 5 активных запросов",
                "ref_link": None
            },
            {
                "number": 4,
                "title": "Предложение альтернативы",
                "description": "Пишем потенциальному клиенту, предлагая альтернативное решение через Kwork",
                "action": "Напишите убедительное предложение",
                "ref_link": None
            },
            {
                "number": 5,
                "title": "Отправка реферальной ссылки",
                "description": "Отправляем свою реферальную ссылку на Kwork",
                "action": "Используйте партнерскую ссылку",
                "ref_link": "https://kwork.ru/ref/13103246",
                "ref_text": "Ссылка на регистрацию Kwork"
            }
        ]
    },
    
    3: {
        "id": "s_targetologi_a",
        "name": "S-таргетологи-A",
        "emoji": "🤖",
        "difficulty": "★★☆",
        "time": "25-35 мин",
        "potential": "1000-5000 руб",
        "description": "Находим маркетологов на Shikari и предлагаем AI-Up",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Регистрируемся в сервисе Shikari",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Регистрация в AI-Up",
                "description": "Регистрируемся в сервисе перехвата заявок AI-Up",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "ref_text": "Ссылка на регистрацию AI-Up"
            },
            {
                "number": 3,
                "title": "Поиск маркетологов",
                "description": "Ищем запросы на маркетологов в разделе 'Интернет-маркетинг'",
                "action": "Найдите активные обсуждения",
                "ref_link": None
            },
            {
                "number": 4,
                "title": "Предложение AI-Up",
                "description": "Предлагаем сервис перехвата заявок как решение проблемы",
                "action": "Напишите коммерческое предложение",
                "ref_link": None
            },
            {
                "number": 5,
                "title": "Отправка реферальной ссылки",
                "description": "Отправляем ссылку на AI-Up",
                "action": "Используйте партнерскую ссылку",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "ref_text": "Ссылка на регистрацию AI-Up"
            }
        ]
    },
    
    4: {
        "id": "s_rabota_online",
        "name": "S-работа онлайн",
        "emoji": "💼",
        "difficulty": "★★☆",
        "time": "20-30 мин",
        "potential": "800-3000 руб",
        "description": "Находим людей, ищущих работу онлайн",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Регистрируемся в сервисе Shikari",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Поиск соискателей",
                "description": "Заходим в раздел 'HR и рекрутинг' на Shikari",
                "action": "Найдите людей, ищущих удаленную работу",
                "ref_link": None
            },
            {
                "number": 3,
                "title": "Предложение инфо-проекта",
                "description": "Предлагаем свой инфо-проект или партнерскую программу",
                "action": "Напишите предложение о сотрудничестве",
                "ref_link": None
            }
        ]
    },
    
    5: {
        "id": "s_master_chas",
        "name": "S-мастер на час",
        "emoji": "👷",
        "difficulty": "★★☆",
        "time": "25-35 мин",
        "potential": "1000-4000 руб",
        "description": "Находим мастеров на час и предлагаем партнерские офферы",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Регистрируемся в сервисе Shikari",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Регистрация в Saleads",
                "description": "Регистрируемся в партнерской сети Saleads",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://saleads.pro/register/75a0d2d0-4d15-11ed-b6cb-099fc6fcedfb",
                "ref_text": "Ссылка на регистрацию Saleads"
            },
            {
                "number": 3,
                "title": "Поиск мастеров",
                "description": "Ищем мастеров по ремонту в разделе 'HR и рекрутинг'",
                "action": "Найдите специалистов по установке кухни, дверей",
                "ref_link": None
            },
            {
                "number": 4,
                "title": "Предложение оффера",
                "description": "Предлагаем партнерский оффер из Saleads",
                "action": "Используйте ссылку на конкретный оффер",
                "ref_link": "https://saleads.pro/lk/webmaster/offer/ed635190-c01d-11ee-abd8-e1437033433c",
                "ref_text": "Ссылка на оффер"
            }
        ]
    },
    
    6: {
        "id": "k_ai_up",
        "name": "K-AI-up",
        "emoji": "📧",
        "difficulty": "★★★",
        "time": "30-40 мин",
        "potential": "1500-6000 руб",
        "description": "Рассылка в формы обратной связи через Kwork + AI-Up",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация на Kwork",
                "description": "Регистрируемся на бирже Kwork",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://kwork.ru/ref/13103246",
                "ref_text": "Ссылка на регистрацию Kwork"
            },
            {
                "number": 2,
                "title": "Регистрация в AI-Up",
                "description": "Регистрируемся в сервисе AI-Up",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "ref_text": "Ссылка на регистрацию AI-Up"
            },
            {
                "number": 3,
                "title": "Поиск услуг рассылок",
                "description": "На Kwork ищем услуги по рассылке в формы обратной связи",
                "action": "Найдите исполнителей",
                "ref_link": "https://kwork.ru/email-marketing/44572442/rassylka-po-formam-obratnoy-svyazi"
            },
            {
                "number": 4,
                "title": "Предложение AI-Up",
                "description": "Пишем исполнителям, предлагая сервис AI-Up",
                "action": "Напишите коммерческое предложение",
                "ref_link": None
            },
            {
                "number": 5,
                "title": "Отправка реферальной ссылки",
                "description": "Отправляем ссылку на AI-Up",
                "action": "Используйте партнерскую ссылку",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "ref_text": "Ссылка на регистрацию AI-Up"
            }
        ]
    },
    
    7: {
        "id": "s_diplomy_vs",
        "name": "S-дипломы-VS",
        "emoji": "🎓",
        "difficulty": "★★☆",
        "time": "20-30 мин",
        "potential": "800-3000 руб",
        "description": "Помощь студентам с дипломами через Shikari + Vsesdal/Studwork",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Регистрируемся в сервисе Shikari",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Поиск студентов",
                "description": "Ищем студентов, которым нужна помощь с учебой в разделе 'Помощь с учебой'",
                "action": "Найдите запросы на написание работ",
                "ref_link": None
            },
            {
                "number": 3,
                "title": "Предложение помощи",
                "description": "Предлагаем помощь через сервисы Vsesdal или Studwork",
                "action": "Напишите предложение о помощи",
                "ref_link": None
            },
            {
                "number": 4,
                "title": "Отправка реферальных ссылок",
                "description": "Отправляем ссылки на образовательные сервисы",
                "action": "Используйте партнерские ссылки",
                "ref_links": [
                    {"name": "Vsesdal", "url": "https://vsesdal.com/about-bonuses", "text": "Ссылка на регистрацию Vsesdal"},
                    {"name": "Studwork", "url": "https://studwork.ru/partner-landing", "text": "Ссылка на регистрацию Studwork"}
                ]
            }
        ]
    },
    
    8: {
        "id": "s_santehniki_ya",
        "name": "S-сантехники-YA",
        "emoji": "🚰",
        "difficulty": "★★☆",
        "time": "25-35 мин",
        "potential": "1000-4000 руб",
        "description": "Находим сантехников через Shikari и направляем на Яндекс.Услуги",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация в Shikari",
                "description": "Регистрируемся в сервисе Shikari",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://shikari.do/promo/?p=196792&email=user@mail.ru&category=1",
                "ref_text": "Ссылка на регистрацию Shikari"
            },
            {
                "number": 2,
                "title": "Поиск мастеров",
                "description": "Ищем мастеров по ремонту в разделе 'Стройка и бытовой ремонт'",
                "action": "Найдите специалистов",
                "ref_link": None
            },
            {
                "number": 3,
                "title": "Регистрация на Яндекс.Услуги",
                "description": "Регистрируемся на Яндекс.Услуги",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://uslugi.yandex.ru/",
                "ref_text": "Ссылка на Яндекс.Услуги"
            },
            {
                "number": 4,
                "title": "Посредничество",
                "description": "Становимся посредником между заказчиком и исполнителем",
                "action": "Предложите свои услуги посредника",
                "ref_link": None
            }
        ]
    },
    
    9: {
        "id": "consenta_k_a_e",
        "name": "Consenta-K-A-E",
        "emoji": "🏢",
        "difficulty": "★★★",
        "time": "40-50 мин",
        "potential": "2000-10000 руб",
        "description": "Комплексная связка для B2B телемаркетинга",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация на Kwork",
                "description": "Регистрируемся на бирже Kwork",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://kwork.ru/ref/13103246",
                "ref_text": "Ссылка на регистрацию Kwork"
            },
            {
                "number": 2,
                "title": "Регистрация в Notisend",
                "description": "Регистрируемся в сервисе email-рассылок",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://app.notisend.ru/ref/JWC2M-MBGGL",
                "ref_text": "Ссылка на регистрацию Notisend"
            },
            {
                "number": 3,
                "title": "Регистрация в AI-Up",
                "description": "Регистрируемся в сервисе AI-Up",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "ref_text": "Ссылка на регистрацию AI-Up"
            },
            {
                "number": 4,
                "title": "Регистрация в Consenta",
                "description": "Регистрируемся в B2B партнерской сети",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://consenta.ru/",
                "ref_text": "Ссылка на регистрацию Consenta"
            },
            {
                "number": 5,
                "title": "Подбор B2B оффера",
                "description": "Подбираем подходящий B2B оффер в Consenta",
                "action": "Изучите доступные офферы",
                "ref_link": None
            }
        ]
    },
    
    10: {
        "id": "g_consenta_k_a_e",
        "name": "G-Consenta-K-A-E",
        "emoji": "🏗️",
        "difficulty": "★★★★",
        "time": "50-60 мин",
        "potential": "3000-20000 руб",
        "description": "Комплексное решение для строительного бизнеса",
        "steps": [
            {
                "number": 1,
                "title": "Регистрация на Kwork",
                "description": "Регистрируемся на бирже Kwork",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://kwork.ru/ref/13103246",
                "ref_text": "Ссылка на регистрацию Kwork"
            },
            {
                "number": 2,
                "title": "Регистрация в Notisend",
                "description": "Регистрируемся в сервисе email-рассылок",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://app.notisend.ru/ref/JWC2M-MBGGL",
                "ref_text": "Ссылка на регистрацию Notisend"
            },
            {
                "number": 3,
                "title": "Регистрация в AI-Up",
                "description": "Регистрируемся в сервисе AI-Up",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://ai-up.ru?ref=f45258cb-162e-4afc-a6b3-e4bb3a373a19",
                "ref_text": "Ссылка на регистрацию AI-Up"
            },
            {
                "number": 4,
                "title": "Регистрация в Consenta",
                "description": "Регистрируемся в B2B партнерской сети",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://consenta.ru/",
                "ref_text": "Ссылка на регистрацию Consenta"
            },
            {
                "number": 5,
                "title": "Регистрация в Gectaro",
                "description": "Регистрируемся в сервисе для строительного бизнеса",
                "action": "Перейдите по ссылке на регистрацию",
                "ref_link": "https://gectaro.com/partners",
                "ref_text": "Ссылка на регистрацию Gectaro"
            }
        ]
    }
}

# ==================== КЛАВИАТУРЫ ====================

def get_main_keyboard():
    """Главное меню"""
    keyboard = VkKeyboard(one_time=False)
    
    keyboard.add_button('🚀 Начать зарабатывать', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    keyboard.add_button('🎯 Все связки (10 шт)', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📝 Оформить ИП', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    keyboard.add_button('ℹ️ Инфо о проекте', color=VkKeyboardColor.SECONDARY)
    
    return keyboard.get_keyboard()

def get_bundles_keyboard():
    """Выбор связки - все 10 связок"""
    keyboard = VkKeyboard(one_time=False)
    
    # Первый ряд
    keyboard.add_button('👨‍🏫 S-репетиторы-F', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('🎯 S-K-таргетологи-K', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    
    # Второй ряд
    keyboard.add_button('🤖 S-таргетологи-A', color=VkKeyboardColor.POSITIVE)
    keyboard.add_button('💼 S-работа онлайн', color=VkKeyboardColor.POSITIVE)
    keyboard.add_line()
    
    # Третий ряд
    keyboard.add_button('👷 S-мастер на час', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('📧 K-AI-up', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    
    # Четвертый ряд
    keyboard.add_button('🎓 S-дипломы-VS', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🚰 S-сантехники-YA', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    
    # Пятый ряд
    keyboard.add_button('🏢 Consenta-K-A-E', color=VkKeyboardColor.PRIMARY)
    keyboard.add_button('🏗️ G-Consenta-K-A-E', color=VkKeyboardColor.PRIMARY)
    keyboard.add_line()
    
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def get_bundle_action_keyboard(bundle_id, step_number, total_steps, has_ref_link=False):
    """Клавиатура для действий в связке"""
    keyboard = VkKeyboard(one_time=False)
    
    if has_ref_link:
        keyboard.add_button('🔗 Перейти по ссылке', color=VkKeyboardColor.POSITIVE)
        keyboard.add_line()
    
    if step_number < total_steps:
        keyboard.add_button('✅ Шаг выполнен', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('➡️ Следующий шаг', color=VkKeyboardColor.PRIMARY)
    else:
        keyboard.add_button('🎉 Завершить связку', color=VkKeyboardColor.POSITIVE)
    
    keyboard.add_line()
    keyboard.add_button('📋 Все шаги связки', color=VkKeyboardColor.SECONDARY)
    keyboard.add_button('◀️ К выбору связки', color=VkKeyboardColor.NEGATIVE)
    
    return keyboard.get_keyboard()

def get_back_keyboard():
    """Простая кнопка назад"""
    keyboard = VkKeyboard(one_time=False)
    keyboard.add_button('◀️ Назад', color=VkKeyboardColor.NEGATIVE)
    return keyboard.get_keyboard()

# ==================== ТЕКСТОВЫЕ ШАБЛОНЫ ====================

def get_welcome_message():
    """Приветственное сообщение с преимуществами"""
    advantages_text = "\n".join(ADVANTAGES)
    
    return f"""🌟 *ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ ПАРТНЕРСКОГО ЗАРАБОТКА* 🌟

Я — твой персональный наставник в мире партнерских программ. 
Моя цель — помочь тебе начать зарабатывать от 500 до 20 000 рублей в день, 
используя готовые схемы и связки.

✨ *ПРЕИМУЩЕСТВА НАШЕЙ СИСТЕМЫ:*

{advantages_text}

🎯 *КАК ЭТО РАБОТАЕТ:*
1. Ты находишь человека, которому что-то нужно
2. Предлагаешь ему решение через партнерский сервис
3. Получаешь процент, когда он платит за услугу
4. Все довольны — ты помог и заработал

💰 *СКОЛЬКО МОЖНО ЗАРАБОТАТЬ:*
• Начинающий: 500-2000 руб/день (первые недели)
• Опытный: 2000-5000 руб/день (через месяц)
• Профессионал: 5000-20000 руб/день (системный подход)

🚀 *ВЫБЕРИ ДЕЙСТВИЕ НИЖЕ ⬇️*"""

# ==================== ОСНОВНОЙ КОД ====================

def main():
    if not GROUP_TOKEN or not GROUP_ID:
        logger.error("Не установлены переменные окружения!")
        return
    
    try:
        vk_session = vk_api.VkApi(token=GROUP_TOKEN)
        vk = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, GROUP_ID)
        
        logger.info(f"Бот запущен! ID группы: {GROUP_ID}")
        
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
                        'registration_time': datetime.now()
                    }
                
                # Главное меню
                if text in ['начать', 'старт', 'start', 'меню', 'привет', 'назад']:
                    vk.messages.send(
                        user_id=user_id,
                        message=get_welcome_message(),
                        keyboard=get_main_keyboard(),
                        random_id=0,
                        dont_parse_links=1
                    )
                
                # Кнопка "Начать зарабатывать"
                elif 'начать зарабатывать' in text:
                    response = (
                        "🎯 *ВЫБЕРИ СВОЙ ПУТЬ К ПЕРВОМУ ЗАРАБОТКУ:*\n\n"
                        "У нас есть *10 готовых связок* разной сложности:\n\n"
                        "★☆☆ *Для новичков:*\n"
                        "• 👨‍🏫 S-репетиторы-F (15-20 мин, 500-2000 руб)\n"
                        "• 💼 S-работа онлайн (20-30 мин, 800-3000 руб)\n\n"
                        "★★☆ *Для опытных:*\n"
                        "• 🎯 S-K-таргетологи-K (25-35 мин, 1000-5000 руб)\n"
                        "• 🤖 S-таргетологи-A (25-35 мин, 1000-5000 руб)\n"
                        "• 🎓 S-дипломы-VS (20-30 мин, 800-3000 руб)\n\n"
                        "★★★ *Для профессионалов:*\n"
                        "• 📧 K-AI-up (30-40 мин, 1500-6000 руб)\n"
                        "• 🏢 Consenta-K-A-E (40-50 мин, 2000-10000 руб)\n\n"
                        "★★★★ *Экспертный уровень:*\n"
                        "• 🏗️ G-Consenta-K-A-E (50-60 мин, 3000-20000 руб)\n\n"
                        "*Какую связку выбираешь?*"
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                
                # Все связки
                elif 'все связки' in text:
                    vk.messages.send(
                        user_id=user_id,
                        message="🎯 *ВСЕ 10 СВЯЗОК ДОСТУПНЫ К ВЫПОЛНЕНИЮ:*",
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                
                # Инфо о проекте
                elif 'инфо' in text or 'о проекте' in text:
                    vk.messages.send(
                        user_id=user_id,
                        message=INFO_MESSAGE,
                        keyboard=get_back_keyboard(),
                        random_id=0,
                        dont_parse_links=1
                    )
                
                # Оформить ИП
                elif 'оформить ип' in text or 'ип' in text:
                    vk.messages.send(
                        user_id=user_id,
                        message=IP_MESSAGE,
                        keyboard=get_back_keyboard(),
                        random_id=0,
                        dont_parse_links=1
                    )
                
                # Обработка выбора связки
                elif any(bundle_name.lower() in text for bundle_name in [
                    's-репетиторы-f', 's-k-таргетологи-k', 's-таргетологи-a',
                    's-работа онлайн', 's-мастер на час', 'k-ai-up',
                    's-дипломы-vs', 's-сантехники-ya', 'consenta-k-a-e',
                    'g-consenta-k-a-e'
                ]):
                    # Определяем выбранную связку
                    bundle_id = None
                    
                    if 's-репетиторы-f' in text:
                        bundle_id = 1
                    elif 's-k-таргетологи-k' in text:
                        bundle_id = 2
                    elif 's-таргетологи-a' in text:
                        bundle_id = 3
                    elif 's-работа онлайн' in text:
                        bundle_id = 4
                    elif 's-мастер на час' in text:
                        bundle_id = 5
                    elif 'k-ai-up' in text:
                        bundle_id = 6
                    elif 's-дипломы-vs' in text:
                        bundle_id = 7
                    elif 's-сантехники-ya' in text:
                        bundle_id = 8
                    elif 'consenta-k-a-e' in text and 'g-' not in text:
                        bundle_id = 9
                    elif 'g-consenta-k-a-e' in text:
                        bundle_id = 10
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        user_progress[user_id]['current_bundle'] = bundle_id
                        user_progress[user_id]['current_step'] = 1
                        
                        # Показываем информацию о связке
                        response = (
                            f"{bundle['emoji']} *{bundle['name']}*\n"
                            f"──────────────────\n"
                            f"📊 Сложность: {bundle['difficulty']}\n"
                            f"⏱ Время: {bundle['time']}\n"
                            f"💰 Потенциал: {bundle['potential']}\n\n"
                            f"*{bundle['description']}*\n\n"
                            f"📋 *ВСЕГО ШАГОВ: {len(bundle['steps'])}*\n\n"
                            f"Готов начать? Переходим к первому шагу!"
                        )
                        
                        # Показываем первый шаг
                        step = bundle['steps'][0]
                        has_ref_link = step.get('ref_link') is not None or step.get('ref_links') is not None
                        
                        step_response = (
                            f"🚀 *ШАГ {step['number']}: {step['title']}*\n"
                            f"──────────────────\n"
                            f"{step['description']}\n\n"
                            f"📌 *ТВОЕ ДЕЙСТВИЕ:*\n"
                            f"{step['action']}"
                        )
                        
                        if step.get('ref_text'):
                            step_response += f"\n\n🔗 *ССЫЛКА:* {step['ref_text']}"
                        
                        keyboard = get_bundle_action_keyboard(
                            bundle_id, 1, len(bundle['steps']), has_ref_link
                        )
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            random_id=0
                        )
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=step_response,
                            keyboard=keyboard,
                            random_id=0
                        )
                
                # К выбору связки
                elif 'к выбору связки' in text:
                    user_progress[user_id]['current_bundle'] = None
                    user_progress[user_id]['current_step'] = 0
                    
                    vk.messages.send(
                        user_id=user_id,
                        message="Выбери связку для выполнения:",
                        keyboard=get_bundles_keyboard(),
                        random_id=0
                    )
                
                # Перейти по ссылке
                elif 'перейти по ссылке' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    current_step = user_progress[user_id]['current_step'] - 1
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        if current_step >= 0 and current_step < len(bundle['steps']):
                            step = bundle['steps'][current_step]
                            
                            if step.get('ref_links'):
                                response = "🔗 *ДОСТУПНЫЕ ССЫЛКИ:*\n\n"
                                for link in step['ref_links']:
                                    response += f"{link['text']}:\n{link['url']}\n\n"
                            elif step.get('ref_link'):
                                response = f"🔗 *ТВОЯ ССЫЛКА:*\n{step['ref_link']}"
                            else:
                                response = "На этом шаге нет ссылки для перехода."
                            
                            response += "\n\n*После перехода вернись в бота!*"
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                random_id=0,
                                dont_parse_links=1
                            )
                
                # Шаг выполнен
                elif 'шаг выполнен' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    current_step = user_progress[user_id]['current_step']
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        
                        if current_step <= len(bundle['steps']):
                            response = f"✅ *Отлично! Шаг {current_step} выполнен!*\n\n"
                            
                            if current_step < len(bundle['steps']):
                                response += "Нажми *'➡️ Следующий шаг'*, чтобы продолжить."
                            else:
                                response += "Ты выполнил все шаги! Нажми *'🎉 Завершить связку'*."
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                random_id=0
                            )
                
                # Следующий шаг
                elif 'следующий шаг' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    current_step_idx = user_progress[user_id]['current_step']
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        
                        if current_step_idx < len(bundle['steps']):
                            step = bundle['steps'][current_step_idx]
                            user_progress[user_id]['current_step'] += 1
                            
                            has_ref_link = step.get('ref_link') is not None or step.get('ref_links') is not None
                            
                            response = (
                                f"🚀 *ШАГ {step['number']}: {step['title']}*\n"
                                f"──────────────────\n"
                                f"{step['description']}\n\n"
                                f"📌 *ТВОЕ ДЕЙСТВИЕ:*\n"
                                f"{step['action']}"
                            )
                            
                            if step.get('ref_text'):
                                response += f"\n\n🔗 *ССЫЛКА:* {step['ref_text']}"
                            
                            keyboard = get_bundle_action_keyboard(
                                bundle_id, step['number'], len(bundle['steps']), has_ref_link
                            )
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                keyboard=keyboard,
                                random_id=0
                            )
                        else:
                            # Все шаги выполнены
                            response = (
                                f"🎉 *ПОЗДРАВЛЯЮ!* Ты выполнил все {len(bundle['steps'])} шагов связки *{bundle['name']}*!\n\n"
                                f"💰 *ПОТЕНЦИАЛЬНЫЙ ЗАРАБОТОК:* {bundle['potential']}\n\n"
                                f"Что дальше?\n"
                                f"1. Повтори связку для закрепления\n"
                                f"2. Выбери новую связку\n"
                                f"3. Оформи ИП для увеличения дохода\n"
                                f"4. Свяжись со мной для получения кода бота"
                            )
                            
                            if bundle_id not in user_progress[user_id]['completed_bundles']:
                                user_progress[user_id]['completed_bundles'].append(bundle_id)
                            
                            vk.messages.send(
                                user_id=user_id,
                                message=response,
                                keyboard=get_main_keyboard(),
                                random_id=0
                            )
                
                # Все шаги связки
                elif 'все шаги связки' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        
                        response = f"📋 *ВСЕ ШАГИ СВЯЗКИ '{bundle['name']}':*\n\n"
                        
                        for i, step in enumerate(bundle['steps'], 1):
                            response += f"{i}. *{step['title']}*\n"
                            if step.get('ref_text'):
                                response += f"   🔗 {step['ref_text']}\n"
                            response += "\n"
                        
                        response += f"*Всего шагов: {len(bundle['steps'])}*"
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            random_id=0
                        )
                
                # Завершить связку
                elif 'завершить связку' in text:
                    bundle_id = user_progress[user_id]['current_bundle']
                    
                    if bundle_id and bundle_id in BUNDLES:
                        bundle = BUNDLES[bundle_id]
                        
                        if bundle_id not in user_progress[user_id]['completed_bundles']:
                            user_progress[user_id]['completed_bundles'].append(bundle_id)
                        
                        completed = len(user_progress[user_id]['completed_bundles'])
                        
                        response = (
                            f"🎉 *СВЯЗКА '{bundle['name']}' ЗАВЕРШЕНА!*\n\n"
                            f"✨ *ТВОИ ДОСТИЖЕНИЯ:*\n"
                            f"• Завершено связок: {completed}\n"
                            f"• Освоена новая ниша\n"
                            f"• Получен опыт работы с партнерками\n\n"
                            f"🚀 *РЕКОМЕНДАЦИИ НА БУДУЩЕЕ:*\n"
                            f"1. Повтори эту связку 2-3 раза\n"
                            f"2. Попробуй другую связку\n"
                            f"3. Оформи ИП для серьезного дохода\n"
                            f"4. Свяжись со мной для масштабирования\n\n"
                            f"*Выбери следующее действие:*"
                        )
                        
                        vk.messages.send(
                            user_id=user_id,
                            message=response,
                            keyboard=get_main_keyboard(),
                            random_id=0
                        )
                        
                        user_progress[user_id]['current_bundle'] = None
                        user_progress[user_id]['current_step'] = 0
    
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}", exc_info=True)

if __name__ == '__main__':
    main()
