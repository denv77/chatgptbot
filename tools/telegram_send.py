"""
 Тестовые методы для работы с Telegram ботом
 В основной программе не используется

 get_chat_id() - если бот недавно куда-то был добавлен
 send_message(message) - отправить тестовое сообщение
"""
from datetime import datetime

import requests

from var.gptbot_env import *

access_token = TELEGRAM_API_KEY_MI
chat_id = GPTD77


def get_chat_id():
    ping_url = 'https://api.telegram.org/bot' + str(access_token) + '/getUpdates'
    response = requests.get(ping_url).json()
    # response_chat_id = response['result'][0]['message']['chat']['id']
    print(f"{datetime.now()} chat_id:", response)


def send_message(message):
    ping_url = 'https://api.telegram.org/bot' + str(access_token) + '/sendMessage?' + \
               'chat_id=' + str(chat_id) + \
               '&parse_mode=Markdown' + \
               '&text=' + message
    response = requests.get(ping_url)
    print(f"{datetime.now()} response:", response, response.text)


get_chat_id()
# send_message("initialization...")

# send_message("start mihal\\_ivanich 3.5.0301-beta")
# send_message("Добрый вечер! Я снова с вами! Ко мне можно обращаться голосовым сообщением, "
#              "я напечатаю его и отвечу на запрос, или "
#              "напрямую через @MihalIvanichBot. Если фраза будет начинаться со слова Нарисуй, то я попробую "
#              "нарисовать ваш запрос. Готов ответить на любые ваши вопросы.")
