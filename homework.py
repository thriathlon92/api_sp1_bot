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
ERROR = 'ошибка запроса "{base_url}", "{headers}", "{params}"! Ошибка {error}'
ERROR1 = ('Ошибка ответа сервера "{base_url}", "{headers}", "{params}"!'
          'Ошибка {response_json}')
ERROR2 = 'Неожиданный ответ {status}'
ERROR_DEBUG = 'Бот столкнулся с ошибкой: {error}'
bot_start_message = 'Я бот и я запустился'


def parse_homework_status(homework):
    homework_name = homework['homework_name']
    status = homework["status"]
    if status not in MESSAGE_DATA:
        raise ValueError(ERROR2.format(status=status))
    verdict = MESSAGE_DATA[status]
    return REVIEWER_ANSWER.format(homework_name=homework_name,
                                  verdict=verdict)


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            BASE_URL, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise ConnectionError(ERROR.format(
            base_url=BASE_URL, headers=HEADERS, params=params, error=error))
    response_json = response.json()
    for key in response_json:
        if key == 'error':
            raise RuntimeError(ERROR1.format(
                base_url=BASE_URL,
                headers=HEADERS,
                params=params,
                response_json=response_json[key]))
        if key == 'code':
            raise RuntimeError(ERROR1.format(
                base_url=BASE_URL,
                headers=HEADERS,
                params=params,
                response_json=response_json[key]))
    return response_json


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
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
        except Exception as error:
            logging.debug(ERROR_DEBUG.format(error=error))
        time.sleep(TIME_SLEEP)


if __name__ == '__main__':
    logging.basicConfig(filename=__file__ + 'main.log', filemode='w')
    main()
