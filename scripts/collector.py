import logging
import asyncio
import uuid

from telegram import Update
from playwright.async_api import async_playwright
from datetime import datetime

from .uprover import data2_uprover , get_data2_file, prepare_data2s
from .report import save_to_csv

from .parm import HOST, COLUMNS_TO_SAVE


def get_page(data2):
    return f'https://pb.nalog.ru/search.html#t=1729599732920&mode=search-ul&queryUl={data2}&mspUl1=1&mspUl2=1&mspUl3=1&page=1&pageSize=10'


async def trigger_captcha(page) -> bool:
    if await page.query_selector('#uniDialog > div > div'):
        return True
    else:
        return False
    

async def get_op_page(data2: str) -> str:
    logging.info(f"Получаем ссылку для data {data2}.")
    
    retry_attempts = 3
    while retry_attempts > 0:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    await page.goto(get_page(data2), timeout=60000, wait_until='domcontentloaded')
                except TimeoutError:
                    logging.warning("Таймаут при подключении. Меняем прокси.")
                    retry_attempts -= 1
                    await browser.close()
                    continue

                if await page.query_selector('selector_captcha'):
                    logging.error('Была обнаружена капча при получении ссылки на страницу. Работа дальше невозможна.')
                    await browser.close
                    return 'No link'
                
                await page.wait_for_selector('selector')
                

                try:
                    link_element = await page.query_selector('selector')
                    if link_element:
                        data_href = str(await link_element.get_attribute('data-href'))
                        if data_href and 'token' in data_href:
                            logging.info(f"Ссылка для data {data2} успешно получена")
                            return HOST+data_href
                        else:
                            logging.warning(f"Ссылка для data {data2} не содержит 'token'.")
                            return 'No link'
                    else:
                        logging.error("Не удалось найти элемент с data-href.")
                        return 'No link'
                except Exception as e:
                    logging.error(f"Ошибка при извлечении ссылки из data-href: {e}")
                    retry_attempts -= 1
            
        except Exception as e:
            logging.error(f"Ошибка при работе get_op_page: {e}")
            retry_attempts -= 1

    logging.error("Все попытки исчерпаны")
    return 'No link'


async def get_op_data(page_url: str) -> list:
    logging.info(f"Начинаем сбор данных с {page_url}.")
    
    if page_url != 'No link':
        retry_attempts = 3
        while retry_attempts > 0:
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    page = await browser.new_page()

                    try:
                        await page.goto(page_url, timeout=60000, wait_until='networkidle')
                    except Exception as e:
                        logging.warning(f"Таймаут или ошибка загрузки страницы: {e}")
                        retry_attempts -= 1
                        await browser.close()
                        continue

                    if await page.query_selector('selector_captcha'):
                        logging.error('Была обнаружена капча при получении данных о field. Работа дальше невозможна.')
                        await browser.close
                        return []

                    await page.wait_for_selector('selector', timeout=10000)

                    # data1
                    try:
                        data1 = await page.locator('selector').text_content()
                        data1 = data1.strip()
                        logging.info(f"Успешно получено data1: {data1}")
                    except Exception as e:
                        data1 = ''
                        logging.error(f"Ошибка при получении наименования: {e}")

                    # data
                    try:
                        data2 = await page.locator('selector').text_content()
                        data2 = data2.strip()
                        logging.info(f"Успешно получено data: {data2}")
                    except Exception as e:
                        data2 = ''
                        logging.error(f"Ошибка при получении data: {e}")

                    # data3
                    try:
                        data3_locator = page.locator("xpath_selector")
                        data3 = await data3_locator.text_content() if await data3_locator.count() > 0 else ''
                        data3 = data3.strip() if len(data3) == 9 else ''
                        logging.info(f"Успешно получено data3: {data3}" if data3 else 'Не получилось найти data3')
                    except Exception as e:
                        data3 = ''
                        logging.error(f"Ошибка при получении data3: {e}")

                    # data4
                    try:
                        data4 = await page.locator('css_selector').nth(0).text_content()
                        data4 = data4.strip()
                        logging.info(f"Успешно получено data4: {data4}")
                    except Exception as e:
                        data4 = ''
                        logging.error(f"Ошибка при получении data4: {e}")

                    # data5
                    try:
                        data5_locator = page.locator("css_selector")
                        data5 = await data5_locator.text_content() if await data5_locator.count() > 0 else ''
                        data5 = data5.strip()
                        logging.info(f"Успешно получен data5: {data5}" if data5 else 'Не удалось найти data5')
                    except Exception as e:
                        data5 = ''
                        logging.error(f"Ошибка при получении data5а: {e}")

                    # data6
                    try:
                        data6 = await page.locator('css_selector').text_content()
                        data6 = data6.strip()
                        logging.info(f"Успешно получено data6: {data6}")
                    except Exception as e:
                        data6 = ''
                        logging.error(f"Ошибка при получении data6: {e}")

                    # data7
                    try:
                        main_block = page.locator("css_selector")
                        text_elements_unsplited = await main_block.all_text_contents()
                        text_elements = text_elements_unsplited[0].split('\n')
                        text_elements = [item.strip() for item in text_elements if item.strip()]

                        # Убираем статичные фразы
                        static_phrases = [
                            '''
                            static_phrases
                            '''
                        ]
                        filtered_text = [text for text in text_elements if text not in static_phrases]

                        data7 = ""
                        data2_data7 = ""

                        # Определение структуры данных
                        if len(filtered_text) == 3:
                            data2_data7 = next((text for text in filtered_text if len(text) == N and text.isdigit()), "")
                            data7_mass = min(filtered_text, key=len)
                            data7 = next((text for text in filtered_text if text != data2_data7 and text != data7_mass), "")

                            logging.info(f"data7: {data7}, data: {data2_data7}")
                        elif len(filtered_text) == 2:
                            data7_mass = min(filtered_text, key=len)
                            data7 = max(filtered_text, key=len)

                            logging.info(f"data7: {data7}")
                        elif len(filtered_text) > 3 and len(filtered_text) % 3 == 0:
                            data7s = []
                            for i in range(0, len(filtered_text), 3):
                                data7 += filtered_text[i] + "\n"
                                data2_data7 += filtered_text[i + 1] + "\n"

                            logging.info(f"Список data7: {data7s}")
                        elif len(filtered_text) > 3 and len(filtered_text) % 2 == 0:
                            data7s = []
                            for i in range(0, len(filtered_text), 2):
                                data7 += filtered_text[i] + "\n"

                            logging.info(f"Список data7 (без data): {data7s}")
                        elif len(filtered_text) > 3 and len(filtered_text) % 5 == 0:
                            for i in range(0, len(filtered_text), 5):
                                data7 += filtered_text[i] + "\n"
                                data2_data7 += filtered_text[i + 1] + "\n" if len(filtered_text[i + 1]) == 12 and filtered_text[i + 1].isdigit() else ""
                                data7 += filtered_text[i + 3] + "\n"
                                data2_data7 += "\n"

                        else:
                            logging.error("Не удалось определить структуру данных")
                    except Exception as e:
                        logging.error(f"Ошибка при получении информации о учредителе: {e}")
                        data7 = ""

                    await browser.close()
                    return [data1, data2, data3, data4, data5, data6, data7]

            except Exception as e:
                logging.error(f"Ошибка при сборе данных организации: {e}")
                retry_attempts -= 1

        logging.error("Не удалось собрать данные после всех попыток.")
        return []
    else:
        logging.error(f'Нет ссылки для сбора данных')
        return []



async def gearbox(filedata1: str, update: Update) -> dict:
    """
    Обрабатывает data из файла и сообщает о прогрессе пользователю.
    """
    file_token = uuid.uuid4().hex[:8]
    result = {"data4": "error", "processed_data2s": 0, "total_data2s": 0, "token" : file_token}

    if data2_uprover(filedata1):
        pause = 60  # seconds
        file_path = get_data2_file(filedata1)

        with open(file_path, mode='r', encoding='utf-8') as data2s_file:
            data2s = data2s_file.readlines()

        pr_data2s = prepare_data2s(data2s)
        total_data2s = len(pr_data2s)
        result["total_data2s"] = total_data2s

        # Рассчитываем точки прогресса
        progress_checkpoints = [
            round(total_data2s * percent / 100) for percent in [30, 50, 60, 90, 100]
        ]
        progress_checkpoints = sorted(set(progress_checkpoints))  # Убираем дубликаты

        all_data = []

        for index, data2 in enumerate(pr_data2s, start=1):
            # Обработка data
            data2_page = await get_op_page(data2)
            call_data = await get_op_data(data2_page)

            if call_data:
                while len(call_data) < len(COLUMNS_TO_SAVE):
                    call_data.append("Не удалось получить данные")
                all_data.append(call_data)
                logging.info(f'[{index}/{total_data2s}] Данные успешно собраны для data {data2}')
            else:
                logging.error(f'[{index}/{total_data2s}] Не удалось собрать данные для data {data2}')
                all_data.append(["Не удалось получить данные"] * len(COLUMNS_TO_SAVE))

            # Обновляем прогресс
            result["processed_data2s"] = index

            # Отправляем сообщение о прогрессе, если достигнута точка
            if index in progress_checkpoints:
                progress = (index / total_data2s) * 100
                await update.message.reply_text(
                    f"Прогресс: {progress:.1f}% (dataов: {index}/{total_data2s})"
                )

            # Проверяем паузу
            if index != total_data2s:
                if index + 1 in progress_checkpoints:
                    logging.info(f'Сообщение о прогрессе будет отправлено перед следующим data.')
                else:
                    logging.info(f'Ожидание {pause} секунд перед обработкой следующего data...')
                    await asyncio.sleep(pause)

        # Сохраняем результат
        todaydate = datetime.now().strftime("%d_%m_%y")
        save_to_csv(data=all_data, file_data1=f'report_{file_token}_{todaydate}.csv')

        result["data4"] = "success"
    else:
        logging.error(f'Файл {filedata1} не прошел проверку на корректность.')

    return result
