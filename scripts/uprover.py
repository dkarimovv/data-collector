import os
import logging

def get_data_file(filename : str):
    current_dir = os.path.dirname(os.path.abspath(__file__))  # Путь к директории текущего скрипта
    file_path = os.path.abspath(os.path.join(current_dir, '..' ,  'tmp', filename))

    return file_path

def get_proxy_file():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.abspath(os.path.join(current_dir, '..' ,  'proxy.txt'))

def data_uprover(filename: str) -> bool:
    path_to_file =  get_data_file(filename)
    fl = False
    try:
        with open(path_to_file, mode='r', encoding='utf-8') as f:
            datas = f.readlines()
        for data in datas:
            data = data.replace('\n' , '')
            if len(data) == 10 and data.isdigit():
                fl = True
            else:
                fl = False
                logging.error(f'Были получены некорректные данные. Проверьте данные в файле {filename}')
                return fl
        
        logging.info('Все данные прошли проверки')
        return fl
    except Exception as e:
        logging.error(f'Произошла непредвиденная ошибка при проверке файла {e}')

def prepare_datas(datas : list) -> list:
    for i in range(len(datas)):
        datas[i] = datas[i].replace('\n' , '')
    return datas
    
if __name__ == '__main__':
    data_uprover('datas.txt')