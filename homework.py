import os
import time
import logging

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

TIME_SLEEP = 1200
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
ERROR_GET_HOMEWORK = ('ошибка запроса "{base_url}",'
                      ' "{headers}", "{params}"! Ошибка {error}')
ERROR_JSON = ('Ошибка ответа сервера "{base_url}", "{headers}", "{params}"!'
              'Ошибка {response_json}')
ERROR_PARSE_HOMEWORK = 'Неожиданный ответ {status}'
ERROR_DEBUG = 'Бот столкнулся с ошибкой: {error}'
BOT_START_MESSAGE = 'Я бот и я запустился'


def parse_homework_status(homework):
    status = homework["status"]
    if status not in MESSAGE_DATA:
        raise ValueError(ERROR_PARSE_HOMEWORK.format(status=status))
    return REVIEWER_ANSWER.format(homework_name=homework['homework_name'],
                                  verdict=MESSAGE_DATA[status])


def get_homework_statuses(current_timestamp):
    params = {'from_date': current_timestamp}
    try:
        response = requests.get(
            BASE_URL, headers=HEADERS, params=params)
    except requests.RequestException as error:
        raise ConnectionError(ERROR_GET_HOMEWORK.format(
            base_url=BASE_URL, headers=HEADERS, params=params, error=error))
    response_json = response.json()
    for key in ['error', 'code']:
        if key in response_json:
            raise RuntimeError(ERROR_JSON.format(
                base_url=BASE_URL,
                headers=HEADERS,
                params=params,
                response_json=response_json[key]))
        return response_json


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot_client = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(BOT_START_MESSAGE)
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
            time.sleep(TIME_SLEEP)
        except Exception as error:
            send_message(message=ERROR_DEBUG.format(error=error),
                         bot_client=bot_client)
            logging.debug(ERROR_DEBUG.format(error=error))


if __name__ == '__main__':
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=FORMAT,
                        level=logging.INFO,
                        filename=__file__ + 'main.log',
                        filemode='w')
    main()
