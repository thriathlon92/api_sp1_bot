import os
import time
import logging

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

TIME_SLEEP = 5
TIME_SLEEP1 = 1200
PRAKTIKUM_TOKEN = os.getenv("PRAKTIKUM_TOKEN")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
BASE_URL = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'}
MESSAGE_DATA = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'reviewing': 'работа взята в ревью',
    'approved': ('Ревьюеру всё понравилось, можно приступать'
                 ' к следующему уроку.'),
}


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    for key in MESSAGE_DATA:
        if homework['status'] == key:
            verdict = MESSAGE_DATA[key]
            return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'
    raise KeyError('ошибка данных')


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    headers = HEADERS
    if current_timestamp is not None:
        try:
            response = requests.get(
                BASE_URL, headers=headers, params=params)
        except requests.RequestException as er:
            raise Exception(f'ошибка: {er}')
        else:
            if response.json().get('error'):
                raise Exception(f'ошибка: ')
            return response.json()
    else:
        print('ошибка данных')


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug('Я бот и я запустился')
    current_timestamp = int(time.time())
    current_timestamp = int(0)
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            logging.info('Отправлено сообщение в чат Telegram')
            time.sleep(TIME_SLEEP1)

        except requests.RequestException as e:
            logging.debug(f'Бот столкнулся с ошибкой: {e}')
            time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    logging.basicConfig(filename='main.log', filemode='w')
    main()
