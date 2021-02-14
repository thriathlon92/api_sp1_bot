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
    'approved': 'Ревьюеру всё понравилось, можно приступать'
                ' к следующему уроку.',
}

REVIEWER_ANSWER = 'У вас проверили работу "{homework_name}"! {verdict}'


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    error1 = f'Ключа {homework["status"]} нет в словаре {MESSAGE_DATA}'
    if homework['status'] not in MESSAGE_DATA:
        raise ValueError(error1)
    verdict = MESSAGE_DATA[homework['status']]
    return REVIEWER_ANSWER.format(homework_name=homework_name,
                                  verdict=verdict)


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    error = f'ошибка запроса {BASE_URL}, {HEADERS}, {params}'
    try:
        response = requests.get(
            BASE_URL, headers=HEADERS, params=params)
    except requests.RequestException as er:
        raise requests.HTTPError(error, er)
    r = response.json()
    if r.get('error') or r.get('code'):
        raise requests.exceptions.HTTPError('Ошибка ответа сервера')
    return r


def send_message(message, bot_client):
    logging.info('Отправлено сообщение в чат Telegram')
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    logging.basicConfig(filename=__file__ + 'main.log', filemode='w')
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    bot_start_message = 'Я бот и я запустился'
    logging.debug(bot_start_message)
    current_timestamp = int(time.time())
    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(new_homework.get('homeworks')[0]),
                    bot_client)
            current_timestamp = new_homework.get('current_date',
                                                 current_timestamp)
            time.sleep(TIME_SLEEP1)

        except requests.RequestException:
            logging.debug(f'Бот столкнулся с ошибкой: {Exception}')
            time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    main()
