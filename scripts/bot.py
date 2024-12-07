import os
import logging
import uuid

from datetime import datetime
from telegram import Update
from configparser import ConfigParser
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from .collector import gearbox

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

config = ConfigParser()
config.read("config.ini")

BOT_API_KEY = config["KEYS"]["bot_api"]
ALLOWED_USERS = set(config["PARAMS"]["users"].split(","))

async def unsupported_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        username = update.effective_user.username or "не указан"
        message_text = update.message.text or "Текст отсутствует"
        logging.warning(f"Пользователь {user_id} (username: {username}) отправил неподдерживаемое сообщение: {message_text}")
        await update.message.reply_text("Бот поддерживает только работу с текстовыми файлами (.txt).")

def start_bot():
    """
    Функция запуска Telegram-бота.
    """
    application = ApplicationBuilder().token(BOT_API_KEY).build()

    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(MessageHandler(filters.Document.ALL, file_handler))

    application.add_handler(MessageHandler(filters.ALL & ~filters.Document.ALL, unsupported_message_handler))

    # Запускаем бота (синхронно)
    logging.info("Бот запущен и ожидает сообщений.")
    application.run_polling()

def ensure_directories():
    for folder in ["tmp", "reports"]:
        if not os.path.exists(folder):
            os.makedirs(folder)

ensure_directories()

# Проверка файла
def validate_txt_file(file_path):
    """
    Проверяет корректность структуры файла.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            lines = file.readlines()
        return all(line.strip().isdigit() and 10 <= len(line.strip()) <= 12 for line in lines)
    except Exception as e:
        logging.error(f"Ошибка проверки файла: {e}")
        return False

# Прогресс обработки
async def report_progress(update, current, total):
    percent = int((current / total) * 100)
    if percent in [30, 50, 70, 90, 100]:
        await update.message.reply_text(f"Прогресс: {percent}% (dataов: {current}/{total}).")

# Обработчик команды /start
async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "не указан"
    logging.info(f"Получена команда /start от пользователя {user_id} (username: {username}).")

    if user_id not in ALLOWED_USERS:
        logging.warning(f"Доступ запрещён для пользователя {user_id} (username: {username}).")
        await update.message.reply_text("У вас нет доступа к использованию бота.")
        return

    logging.info(f"Пользователь {user_id} (username: {username}) авторизован. Отправляю приветственное сообщение.")
    await update.message.reply_text("Отправьте текстовый файл с dataами для обработки.")


# Обработчик получения файла
async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "не указан"
    document = update.message.document

    # Проверяем, что документ существует
    if not document:
        logging.warning(f"Пользователь {user_id} (username: {username}) отправил сообщение без файла.")
        await update.message.reply_text("Пожалуйста, отправьте текстовый файл с расширением .txt.")
        return

    # Проверяем имя файла
    if not document.file_name:
        logging.warning(f"Пользователь {user_id} (username: {username}) отправил файл без имени.")
        await update.message.reply_text("Файл должен иметь имя с расширением .txt.")
        return

    # Проверяем расширение файла
    if not document.file_name.endswith(".txt"):
        logging.warning(f"Пользователь {user_id} (username: {username}) отправил файл с недопустимым расширением: {document.file_name}.")
        await update.message.reply_text("Пожалуйста, отправьте текстовый файл с расширением .txt.")
        return

    if user_id not in ALLOWED_USERS:
        logging.warning(f"Доступ запрещён для пользователя {user_id} (username: {username}).")
        await update.message.reply_text("У вас нет доступа к использованию бота.")
        return

    if not document.file_name.endswith(".txt"):
        logging.warning(f"Пользователь {user_id} (username: {username}) отправил файл с недопустимым расширением: {document.file_name}.")
        await update.message.reply_text("Пожалуйста, отправьте текстовый файл с расширением .txt.")
        return

    original_filename = os.path.basename(document.file_name)
    unique_suffix = uuid.uuid4().hex[:8]
    file_name = f"{unique_suffix}_{original_filename}"
    file_path = os.path.join("tmp", file_name)

    try:
        # Получаем объект файла и сохраняем его
        file = await context.bot.get_file(document.file_id)
        await file.download_to_drive(file_path)
        logging.info(f"Файл {file_name} от пользователя {user_id} (username: {username}) загружен в {file_path}.")

        # Проверка файла
        if not validate_txt_file(file_path):
            logging.warning(f"Файл {file_name} от пользователя {user_id} (username: {username}) не прошёл проверку.")
            await update.message.reply_text("Файл содержит некорректные данные. Попробуйте ещё раз.")
            return
        
        await update.message.reply_text("Ваш файл успешно загружен и добавлен в очередь на обработку.")

        # Обрабатываем файл
        logging.info(f"Начинается обработка файла {file_name} для пользователя {user_id} (username: {username}).")
        await update.message.reply_text("Ваш файл взят в обработку. Пожалуйста, подождите...")
        result = await gearbox(file_name, update)

        if result["status"] == "success":
            logging.info(f"Обработка файла {file_name} завершена успешно для пользователя {user_id} (username: {username}).")
            for progress in [30, 50, 70, 90, 100]:
                await report_progress(update, result["processed_inns"] * progress // 100, result["total_inns"])

            todaydate = datetime.now().strftime("%d_%m_%y")
            report_path = os.path.join("reports", f"report_{result['token']}_{todaydate}.csv")
            await update.message.reply_text("Обработка завершена. Отправляю файл.")
            logging.info(f"Отправка файла {report_path} пользователю {user_id} (username: {username}).")
            await context.bot.send_document(chat_id=update.effective_chat.id, document=open(report_path, "rb"))
        else:
            logging.error(f"Ошибка обработки файла {file_name} для пользователя {user_id} (username: {username}).")
            await update.message.reply_text("Ошибка при обработке файла. Проверьте формат или повторите позже.")
    except Exception as e:
        logging.error(f"Ошибка при обработке файла {file_name} от пользователя {user_id} (username: {username}): {e}")
        await update.message.reply_text("Произошла ошибка. Попробуйте позже.")
    finally:
        # Удаление временного файла
        if os.path.exists(file_path):
            os.remove(file_path)
            logging.info(f"Файл {file_path} удалён после обработки для пользователя {user_id} (username: {username}).")



