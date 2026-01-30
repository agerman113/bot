import vk_api
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import logging
import os

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Получение данных из переменных окружения
GROUP_TOKEN = os.getenv('VK_GROUP_TOKEN')
GROUP_ID = os.getenv('VK_GROUP_ID')

# Проверка наличия токена и ID группы
if not GROUP_TOKEN or not GROUP_ID:
    logger.error("Токен или ID группы не установлены! Проверьте переменные окружения.")
    exit(1)

# Инициализация API VK
try:
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkBotLongPoll(vk_session, GROUP_ID)
    logger.info(f"Бот запущен и слушает события для группы ID: {GROUP_ID}")
except Exception as e:
    logger.error(f"Ошибка при инициализации: {e}")
    exit(1)

# Основной цикл обработки событий
def main():
    for event in longpoll.listen():
        try:
            # Обработка нового сообщения
            if event.type == VkBotEventType.MESSAGE_NEW:
                user_id = event.obj.message['from_id']
                message_text = event.obj.message['text'].lower()
                
                # Логируем полученное сообщение
                logger.info(f"Получено сообщение от {user_id}: {message_text}")
                
                # Приветствие на команды
                if message_text in ['привет', 'старт', 'начать', 'hello', 'hi']:
                    user_info = vk.users.get(user_ids=user_id)[0]
                    user_name = user_info['first_name']
                    
                    response = (
                        f"Привет, {user_name}! 👋\n\n"
                        f"Это тестовый бот. Твой ID: {user_id}\n"
                        f"Напиши 'команды' для получения списка доступных команд."
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=response,
                        random_id=0
                    )
                    logger.info(f"Отправлен приветственный ответ пользователю {user_id}")
                
                # Показ доступных команд
                elif message_text in ['команды', 'помощь', 'help']:
                    commands_list = (
                        "Доступные команды:\n"
                        "• 'привет' - приветствие\n"
                        "• 'команды' - этот список\n"
                        "• 'тест' - проверка работы\n"
                        "• 'id' - узнать свой ID"
                    )
                    
                    vk.messages.send(
                        user_id=user_id,
                        message=commands_list,
                        random_id=0
                    )
                
                # Простой тест
                elif message_text == 'тест':
                    vk.messages.send(
                        user_id=user_id,
                        message="✅ Бот работает корректно!",
                        random_id=0
                    )
                
                # Показ ID пользователя
                elif message_text == 'id':
                    vk.messages.send(
                        user_id=user_id,
                        message=f"Твой ID: {user_id}",
                        random_id=0
                    )
        
        except Exception as e:
            logger.error(f"Ошибка при обработке события: {e}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")