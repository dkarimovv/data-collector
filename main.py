import logging
import asyncio

# from scripts.collector import gearbox
from scripts.bot import start_bot



def init_logs():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)  # Устанавливаем уровень логирования

    httpx_logger = logging.getLogger("httpx")
    httpx_logger.setLevel(logging.CRITICAL)
    
    # Обработчик для записи логов в файл
    if not logger.hasHandlers():
        file_handler = logging.FileHandler('logs.txt', mode='a')
        file_handler.setLevel(logging.INFO)

        # Обработчик для вывода логов в консоль
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Формат логов
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Отключаем вывод логов от httpx
        

        # Добавляем обработчики к основному логгеру
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    logging.info('Логирование было успешно инициализировано')



if __name__ == '__main__':
    init_logs()
    asyncio.run(start_bot())