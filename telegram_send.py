import requests

from gptbotenv import *

access_token = TELEGRAM_API_KEY
chat_id = GPTD77


def get_chat_id():
    ping_url = 'https://api.telegram.org/bot' + str(access_token) + '/getUpdates'
    response = requests.get(ping_url).json()
    response_chat_id = response['result'][0]['message']['chat']['id']
    print("chat_id:", response_chat_id)


def send_message(message):
    ping_url = 'https://api.telegram.org/bot' + str(access_token) + '/sendMessage?' + \
               'chat_id=' + str(chat_id) + \
               '&parse_mode=Markdown' + \
               '&text=' + message
    response = requests.get(ping_url)
    print("response:", response, response.text)


send_message("initialization...")

# send_message("start mihal\\_ivanich 3.5.0301-beta")
# send_message("Добрый вечер! Я снова с вами! Ко мне можно обращаться голосовым сообщением, "
#              "я напечатаю его и отвечу на запрос, или "
#              "напрямую через @MihalIvanichBot. Если фраза будет начинаться со слова Нарисуй, то я попробую "
#              "нарисовать ваш запрос. Готов ответить на любые ваши вопросы.")
