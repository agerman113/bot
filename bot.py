import os
import time
import logging

# Настройка логирования в файл
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/app/data/bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=" * 50)
    logger.info("БОТ ЗАПУЩЕН!")
    
    # Проверяем переменные окружения
    token = os.getenv('VK_GROUP_TOKEN')
    group_id = os.getenv('VK_GROUP_ID')
    
    logger.info(f"Токен: {'УСТАНОВЛЕН' if token else 'НЕ УСТАНОВЛЕН'}")
    logger.info(f"ID группы: {group_id if group_id else 'НЕ УСТАНОВЛЕН'}")
    
    if not token or not group_id:
        logger.error("ОШИБКА: Отсутствуют переменные окружения!")
        logger.error("Добавьте VK_GROUP_TOKEN и VK_GROUP_ID в настройках Bothost")
        # Не завершаем работу, чтобы видеть ошибку в логах
        while True:
            time.sleep(60)
    
    logger.info("=" * 50)
    
    try:
        import vk_api
        from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
        
        logger.info("Библиотеки импортированы успешно")
        
        # Инициализация
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        longpoll = VkBotLongPoll(vk_session, group_id)
        
        logger.info(f"Бот подключен к группе ID: {group_id}")
        logger.info("Ожидание сообщений...")
        
        # Простой цикл
        for event in longpoll.listen():
            if event.type == VkBotEventType.MESSAGE_NEW:
                msg = event.obj.message
                user_id = msg['from_id']
                text = msg['text']
                
                logger.info(f"Получено: {text} от {user_id}")
                
                if text.lower() == 'привет':
                    vk.messages.send(
                        user_id=user_id,
                        message="Привет! Я работаю!",
                        random_id=0
                    )
                    logger.info(f"Отправлен ответ пользователю {user_id}")
    
    except Exception as e:
        logger.error(f"КРИТИЧЕСКАЯ ОШИБКА: {e}", exc_info=True)
        # Держим процесс запущенным, чтобы увидеть ошибку
        while True:
            time.sleep(60)

if __name__ == '__main__':
    main()
