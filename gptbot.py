import os
import subprocess
from typing import Any

import openai
import speech_recognition as sr
import telebot

from gptbotenv import *

# print_enable = True
print_enable = False

bot = telebot.TeleBot(TELEGRAM_API_KEY)
openai.api_key = OPENAI_API_KEY
r = sr.Recognizer()

init_role_family = {'role': 'system', 'content': 'Тебя зовут Михал Иваныч. Ты очень веселый мужчина средних лет. Ты являешься экспертом в области кулинарии, садоводства и уборки'}

init_role_lk_egais = {'role': 'system', 'content': 'Тебя зовут Михал Иваныч. Ты очень веселый мужчина средних лет. Ты являешься сотрудником компании ЦентрИнформ и экспертом в области алкогольной продукции и разработки ПО'}
groups_messages = {
    FAMILY: [],
    ULIA: [],
    GPTD77: [],
    DENIS: [],
    LK_EGAIS: []
}

groups_messages_length = {
    FAMILY: [],
    ULIA: [],
    GPTD77: [],
    DENIS: [],
    LK_EGAIS: []
}


def check_auth(chat_id):
    messages = groups_messages.get(chat_id)
    return messages is not None


def print_if(*args: Any):
    if print_enable:
        print(*args)


def get_messages(chat_id):
    return groups_messages.get(chat_id)


def add_message(chat_id, content):
    messages = groups_messages.get(chat_id)
    messages.append(content)
    messages_length = groups_messages_length.get(chat_id)
    messages_length.append(len(content["content"].split()))
    # Максимум 4096 токенов. 1000 токенов - это примерно 750 слов
    while sum(messages_length) >= 3000 or len(messages) >= 100:
        del messages[1]
        del messages_length[1]


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = str(message.chat.id)
    if not check_auth(chat_id):
        return f"Ваш chat_id:{chat_id} не зарегистрирован"

    print_if("voice message:", message)
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # file_oga = "/Users/den/Projects/test/chatgptbot/data/" + message.voice.file_unique_id + ".oga"
    file_oga = "/home/gptchatbot/data/" + message.voice.file_unique_id + ".oga"

    with open(file_oga, "wb") as ogg:
        ogg.write(downloaded_file)

    text = recognize_voice(file_oga)
    os.remove(file_oga)
    bot.reply_to(message, text)

    response_text = handle(chat_id, text)
    bot.reply_to(message, response_text)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = str(message.chat.id)
    if not check_auth(chat_id):
        return f"Ваш chat_id:{chat_id} не зарегистрирован"

    print_if("text message:", message)

    user_text = message.text.strip()

    # if chat_id != DENIS:
    #     return

    if not user_text.startswith("@MihalIvanichBot"):
        add_message(chat_id, {"role": "user", "content": user_text})
        return

    user_text = user_text.replace("@MihalIvanichBot", "", 1).lstrip()

    response_text = handle(chat_id, user_text)

    bot.reply_to(message, response_text)


def handle(chat_id, user_text):
    if user_text.lower().startswith("нарисуй"):
        return send_to_gpt_image(user_text)

    add_message(chat_id, {"role": "user", "content": user_text})
    response_text = send_to_gpt_chat(get_messages(chat_id))
    add_message(chat_id, {"role": "assistant", "content": response_text})
    return response_text


def send_to_gpt_chat(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        max_tokens=1024,
        # temperature=0.3,
        # top_p=1,
        # frequency_penalty=0,
        # presence_penalty=0
    )
    print_if("response chat:", response)
    print_if("response chat text:", response.choices[0].message.content)
    return response.choices[0].message.content


def send_to_gpt_image(message):
    response = openai.Image.create(
        prompt=message,
        size="1024x1024"
    )
    print_if("response image:", response.data[0].url)
    return response.data[0].url


def recognize_voice(file_oga):
    file_wav = file_oga + ".wav"

    subprocess.run(['ffmpeg', '-v', 'quiet', '-i', file_oga, file_wav])

    with open(file_wav, "rb") as wav:
        user_audio_file = sr.AudioFile(wav)
        with user_audio_file as source:
            user_audio = r.record(source)
    text = r.recognize_google(user_audio, language='ru-RU')
    print_if("voice recognized text:", text)
    os.remove(file_wav)
    return text


add_message(FAMILY, init_role_family)
add_message(ULIA, init_role_family)
add_message(GPTD77, init_role_lk_egais)
add_message(DENIS, init_role_lk_egais)
add_message(LK_EGAIS, init_role_lk_egais)

# Start the bot
# bot.polling()
bot.infinity_polling()
