import asyncio
import aiohttp
import sys
import string
import logging

from .uprover import get_proxy_file
from .parm import HOST

def handle_proxy_list(rst, proxies_list):
    for i in proxies_list:
        if '@' in i:
            userdata, ipport = i.split('@')
            if list(string.ascii_lowercase) in userdata:
                pass
            else:
                userdata, ipport = ipport, userdata
            usr, pas = userdata.split(':')
            ip, port = ipport.split(':')
            rst.append(f'{ip}:{port}:{usr}:{pas}')
        elif ':' in i:
            parts = i.split(':')
            if len(parts) == 4:
                ip, port, usr, pas = parts
                if ip and port and usr and pas:
                    print(f'Были полученны прокси {i}')
                if '.' in ip:
                    rst.append(f'{ip}:{port}:{usr}:{pas}')
                elif '.' in port:
                    ip, port = port, ip
                    rst.append(f'{ip}:{port}:{usr}:{pas}')
                else:
                    ip, port, usr, pas = usr, pas, ip, port
                    if '.' in ip:
                        rst.append(f'{ip}:{port}:{usr}:{pas}')
                    elif '.' in port:
                        ip, port = port, ip
                        usr, pas = pas, usr
                        rst.append(f'{ip}:{port}:{usr}:{pas}')
        else:
            print('''Неизвестный тип прокси. Поддерживается только следующие виды:
                1) IP:PORT:USERNAME:PASSWORD
                2) IP:PORT@USERNAME:PASSWORD
                3) USERNAME:PASSWORD:IP:PORT
                4) USERNAME:PASSWORD@IP:PORT
            ''')

    return rst  # Важно вернуть rst, чтобы handy_proxies получила обновлённый список

async def handy_proxies():
    print('Не удалось автоматически получить прокси. Введите прокси вручную')
    proxies_input = await asyncio.to_thread(input, 'Введите прокси через запятую или пробел: ')
    rst = []
    if len(proxies_input) > 0:
        if ',' in proxies_input:
            proxies_list = proxies_input.split(',')
        elif ' ' in proxies_input:
            proxies_list = proxies_input.split(' ')
        else:
            print('Были введены некорректные данные')
            sys.exit(1)

        rst = handle_proxy_list(rst, proxies_list)
        print(rst)
        return rst  # Вернём rst после вызова handle_proxy_list
    else:
        print('Error no data were inputed')
        return None


async def get_proxies(file_path=get_proxy_file()) -> list:
    """Получение прокси из файла с проверкой их доступности."""
    with open(file_path, "r+") as f:
        lines = f.readlines()
        print(lines)

        if not lines:
            print("Файл прокси пуст. Получаем прокси вручную.")
            lines = await handy_proxies()
            print(f'lines: {lines}')

        used_proxy_index = -1
        for i, line in enumerate(lines):
            if line.strip().endswith("*"):
                used_proxy_index = i
                break

        if used_proxy_index == -1:
            next_proxy_index = 0
        else:
            next_proxy_index = (used_proxy_index + 1) % len(lines)

        proxy = lines[next_proxy_index].strip().replace("*", "").strip()
        proxy_parts = proxy.split(':')
        proxy_dict = [proxy_parts[0], proxy_parts[1], proxy_parts[2], proxy_parts[3]]  # Прокси разделены на части
        print(proxy_dict)


        # Проверяем доступность текущего прокси
        if not await check_proxy(proxy_dict):
            print(f"Прокси {proxy_dict[0]} не работает. Ищем следующий прокси.")
            
            # Удаляем метку `*` у текущего прокси, если она есть
            if used_proxy_index != -1:
                lines[used_proxy_index] = lines[used_proxy_index].replace(" *", "").strip() + "\n"

            # Переходим к следующему прокси
            next_proxy_index = (next_proxy_index + 1) % len(lines)
            f.seek(0)
            f.writelines(lines)
            f.truncate()
            
            # Повторяем процесс с другим прокси
            return await get_proxies(file_path)

        # Обновляем метки прокси в файле
        if used_proxy_index != -1:
            lines[used_proxy_index] = lines[used_proxy_index].replace(" *", "").strip() + "\n"
        lines[next_proxy_index] = proxy + " *\n"

        f.seek(0)
        f.writelines(lines)
        f.truncate()

        return proxy_dict


async def check_proxy(proxy):
    """ Проверяем работоспособность прокси через подключение к известному сайту с использованием HTTP. """
    proxy_url = f"http://{proxy[2]}:{proxy[3]}@{proxy[0]}:{proxy[1]}"  # Формат для HTTP-прокси
    proxy_auth = aiohttp.BasicAuth(proxy[2], proxy[3])
    logging.info(f"Проверяем прокси {proxy_url}.")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(HOST, proxy=proxy_url, proxy_auth=proxy_auth, timeout=10):
                logging.info(f"Прокси {proxy_url} работает.")
                return True
    except Exception as e:
        logging.error(f"Прокси {proxy_url} не работает. Ошибка: {e}")
        return False