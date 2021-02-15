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
ERROR = 'ошибка запроса "{base_url}", "{headers}", {params}'
ERROR1 = 'Ошибка ответа сервера "{base_url}", "{headers}", {params}'
logging.info('Отправлено сообщение в чат Telegram')


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework["status"]
    error1 = f'Неожиданный ответ {status}'
    if status not in MESSAGE_DATA:
        raise ValueError(error1)
    verdict = MESSAGE_DATA[status]
    return REVIEWER_ANSWER.format(homework_name=homework_name,
                                  verdict=verdict)


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            BASE_URL, headers=HEADERS, params=params)
    except requests.RequestException as er:
        raise ConnectionError(ERROR.format(
            base_url=BASE_URL, headers=HEADERS, params=params), f'ошибка:{er}')
    r = response.json()
    print(r)
    for key in r:
        if key == ('error' or 'code'):
            raise RuntimeError(ERROR1.format(
                base_url=BASE_URL, headers=HEADERS, params=params),
                f'ошибка {r[key]}')
    return r


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    bot_start_message = 'Я бот и я запустился'
    logging.debug(bot_start_message)
    current_timestamp = int(time.time())
    current_timestamp = 0
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

        except requests.RequestException as er:
            logging.debug(f'Бот столкнулся с ошибкой: {er}')
            raise Exception(f'Бот столкнулся с ошибкой: {er}')
        time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    logging.basicConfig(filename=__file__ + 'main.log', filemode='w')
    main()
