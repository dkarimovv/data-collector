import logging
import os

import pandas as pd
from .parm import COLUMNS_TO_SAVE


def save_to_csv(data, file_name='output.csv'):
    try:
        
        # Преобразуем данные в DataFrame с учетом заданных столбцов
        df = pd.DataFrame(data, columns=COLUMNS_TO_SAVE)
        
        # Проверяем существование папки reports
        reports_dir = os.path.join(os.getcwd(), "reports")
        if not os.path.exists(reports_dir):
            os.makedirs(reports_dir)
        
        # Сохраняем файл в папку reports
        full_path = os.path.join(reports_dir, file_name)
        df.to_csv(full_path, index=False, encoding='utf-8')
        logging.info(f"Данные успешно сохранены в файл {full_path}.")
    except Exception as e:
        logging.error(f"Ошибка при сохранении данных: {e}")