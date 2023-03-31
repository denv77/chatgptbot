import os
import subprocess

import openai
import speech_recognition as sr
import telebot

from gptbotenv import *

bot = telebot.TeleBot(TELEGRAM_API_KEY)
openai.api_key = OPENAI_API_KEY
r = sr.Recognizer()

init_role_family = {'role': 'system', 'content': 'Тебя зовут Михал Иваныч. Ты являешься экспертом в области '
                                                 'кулинарии, садоводства и уборки'}

init_role_lk_egais = {'role': 'system', 'content': 'Тебя зовут Михал Иваныч. Ты являешься сотрудником компании '
                                                   'ЦентрИнформ и экспертом в области алкогольной продукции и '
                                                   'разработки ПО'}
groups_messages = {
    FAMILY: [init_role_family],
    ULIA: [init_role_family],
    GPTD77: [init_role_lk_egais],
    DENIS: [init_role_lk_egais],
    LK_EGAIS: [init_role_lk_egais]
}


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    print("voice message:", message)
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # file_oga = "/Users/den/Projects/test/chatgptbot/data/" + message.voice.file_unique_id + ".oga"
    file_oga = "/home/gptchatbot/data/" + message.voice.file_unique_id + ".oga"

    with open(file_oga, "wb") as ogg:
        ogg.write(downloaded_file)

    text = recognize_voice(file_oga)
    os.remove(file_oga)

    bot.reply_to(message, text)

    response_text = handle(str(message.chat.id), text)

    bot.reply_to(message, response_text)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_text = message.text.strip()

    # if str(message.chat.id) != DENIS:
    #     return
    if not user_text.startswith("@MihalIvanichBot"):
        return

    # print("text message:", message)
    user_text = user_text.replace("@MihalIvanichBot", "", 1).lstrip()

    response_text = handle(str(message.chat.id), user_text)

    bot.reply_to(message, response_text)


def handle(chat_id, user_text):
    if user_text.lower().startswith("нарисуй"):
        return send_to_gpt_image(user_text)

    messages = groups_messages[chat_id]
    if messages is None:
        messages = []
        groups_messages[chat_id] = messages

    messages.append({"role": "user", "content": user_text})

    if len(messages) >= 14:
        # messages.pop(1)
        del messages[1:3]

    response_text = send_to_gpt_chat(messages)
    messages.append({"role": "assistant", "content": response_text})
    return response_text


def send_to_gpt_chat(messages):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.5,
        max_tokens=1024,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    # print("response chat:", response)
    # print("response chat text:", response.choices[0].message.content)
    return response.choices[0].message.content


def send_to_gpt_image(message):
    response = openai.Image.create(
        prompt=message,
        size="1024x1024"
    )
    # print("response image:", response.data[0].url)
    return response.data[0].url


def recognize_voice(file_oga):
    file_wav = file_oga + ".wav"

    subprocess.run(['ffmpeg', '-v', 'quiet', '-i', file_oga, file_wav])

    with open(file_wav, "rb") as wav:
        user_audio_file = sr.AudioFile(wav)
        with user_audio_file as source:
            user_audio = r.record(source)
    text = r.recognize_google(user_audio, language='ru-RU')
    # print("voice recognized text:", text)
    os.remove(file_wav)
    return text


# Start the bot
# bot.polling()
bot.infinity_polling()
