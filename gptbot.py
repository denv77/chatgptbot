import argparse
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import telebot
import yaml

import var.gptbot_env as var
from config_init_roles import *
from gptbot_openai import GptBotOpenAI
from gptbot_voice_recognizer import GptBotVoiceRecognizer
from tools.proxy_api import ProxyApi

openai = GptBotOpenAI(var.OPENAI_API_KEY, var.OPENAI_API_URL)
voice_recognizer = GptBotVoiceRecognizer()
proxy_api = ProxyApi(var.OPENAI_API_KEY)

# Хранит контекст последнего общения группы с ботом
groups_messages = {
    var.FAMILY: [],
    var.ULIA: [],
    var.GPTD77: [],
    var.DENIS: [],
    var.SIA: [],
    var.SIA_M: [],
    var.LK_EGAIS: [],
    var.TECH: []
}

# Хранит длины сообщений. Нужно для подсчета размера контекста
groups_messages_length = {
    var.FAMILY: [],
    var.ULIA: [],
    var.GPTD77: [],
    var.DENIS: [],
    var.SIA: [],
    var.SIA_M: [],
    var.LK_EGAIS: [],
    var.TECH: []
}

# Маппинг названия группы на идентификатор
groups_names = {
    "FAMILY": var.FAMILY,
    "SIA": var.SIA,
    "SIA_M": var.SIA_M,
    "ULIA": var.ULIA,
    "GPTD77": var.GPTD77,
    "DENIS": var.DENIS,
    "LK_EGAIS": var.LK_EGAIS,
    "TECH": var.TECH
}

print(f"{datetime.now()} starting...")

parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", help="path to config file", type=str)
parsed_args = parser.parse_args()
print(f"{datetime.now()} args:", parsed_args)
print(f"{datetime.now()} args.config:", parsed_args.config)

base_dir = os.path.dirname(os.path.realpath(__file__))
config_path = f"{base_dir}/config.yaml"
tegram_data_dir_path = f"{base_dir}/data"
if parsed_args.config:
    config_path = Path(parsed_args.config).resolve()
    tegram_data_dir_path = f"{config_path.parent}/data"

print(f"{datetime.now()} base_dir:", base_dir)
print(f"{datetime.now()} config_path:", config_path)
print(f"{datetime.now()} tegram_data_dir_path:", tegram_data_dir_path)
print(f"{datetime.now()} sys.path[0]:", sys.path[0])

with open(config_path, "r") as f:
    config = yaml.safe_load(f)
os.makedirs(tegram_data_dir_path, exist_ok=True)

print(f"{datetime.now()} config: {json.dumps(config, indent=4)}")
gpt_chat_settings = config["gpt_chat_settings"]
gpt_image_settings = config["gpt_image_settings"]
print_enable = config["app_settings"]["print_enable"]
bot_name = config["app_settings"]["bot_name"]

if bot_name == "DV":
    telegram_api_key = var.TELEGRAM_API_KEY_DV
    telegram_bot_id = var.TELEGRAM_BOT_ID_DV
    init_role = init_role_denis
elif bot_name == "SIA":
    telegram_api_key = var.TELEGRAM_API_KEY_SIA
    telegram_bot_id = var.TELEGRAM_BOT_ID_SIA
    init_role = init_role_sia
elif bot_name == "MI":
    telegram_api_key = var.TELEGRAM_API_KEY_MI
    telegram_bot_id = var.TELEGRAM_BOT_ID_MI
    init_role = init_role_lk_egais
elif bot_name == "A":
    telegram_api_key = var.TELEGRAM_API_KEY_A
    telegram_bot_id = var.TELEGRAM_BOT_ID_A
    init_role = init_role_family
else:
    raise Exception(f"bot_name not found: {bot_name}")

bot = telebot.TeleBot(telegram_api_key)

print(f"{datetime.now()} bot: {json.dumps(bot.get_me().to_dict(), indent=4)}")


def check_auth(chat_id):
    messages = groups_messages.get(chat_id)
    return messages is not None


def print_if(*args: Any):
    if print_enable:
        print(f"{datetime.now()} [DEBUG]", *args)


def system_settings(settings_str):
    print(f"{datetime.now()} system_settings:", settings_str)

    msg = settings_str.split(":", 2)

    info_msg = "system:\n" \
               "  balance\n" \
               "  info\n" \
               "  [reset|hard_reset]:GROUP_NAME\n" \
               "  [settings_chat|settings_image]:{}\n" \
               "  add:{name,role:[system|user|assistant],content}"
    if settings_str == "system" or len(msg) < 2:
        return info_msg

    if msg[1] == "balance":
        return proxy_api.balance()

    if msg[1] == "info":
        all_counts = {}
        for name in groups_names:
            all_counts[name] = f'size: {len(groups_messages.get(groups_names.get(name)))} ' \
                               f'words: {sum(groups_messages_length.get(groups_names.get(name)))}'
        return f'{gpt_chat_settings}\n\n{gpt_image_settings}\n\n{groups_names}\n\n{all_counts}\n\n{init_role}'

    if msg[1] == "reset" or msg[1] == "hard_reset":
        chat_id = groups_names.get(msg[2])
        messages = groups_messages.get(chat_id)
        messages_length = groups_messages_length.get(chat_id)
        if msg[1] == "reset":
            del messages[1:]
            del messages_length[1:]
        else:
            del messages[0:]
            del messages_length[0:]
            add_message(chat_id, init_role)
        return f"{msg[2]} size: {len(messages)} words: {sum(messages_length)} init: {messages[0]['content']}"

    if msg[1] == "add":
        try:
            add = json.loads(msg[2])
            chat_id = groups_names.get(add["name"])
            if add["role"] not in ["system", "user", "assistant"]:
                add["role"] = "system"
            content = {'role': add["role"], 'content': add["content"]}
            messages = groups_messages.get(chat_id)
            messages_length = groups_messages_length.get(chat_id)
            if add["role"] == "system":
                del messages[0:]
                del messages_length[0:]
            messages.append(content)
            messages_length.append(len(add["content"].split()))

            return f"{add['name']} size: {len(messages)} words: {sum(messages_length)}"
        except Exception as e:
            traceback.print_exc()
            return str(repr(e))

    if msg[1] == "settings_chat":
        try:
            settings_chat = json.loads(msg[2])
            for k in settings_chat:
                gpt_chat_settings[k] = settings_chat[k]
                config["gpt_chat_settings"] = gpt_chat_settings
            with open(config_path, "w") as cfg_file:
                yaml.dump(config, cfg_file)
            return f'{gpt_chat_settings}'
        except Exception as e:
            traceback.print_exc()
            return str(repr(e))
    if msg[1] == "settings_image":
        try:
            settings_image = json.loads(msg[2])
            for k in settings_image:
                gpt_image_settings[k] = settings_image[k]
                config["gpt_image_settings"] = gpt_image_settings
            with open(config_path, "w") as cfg_file:
                yaml.dump(config, cfg_file)
            return f'{gpt_image_settings}'
        except Exception as e:
            traceback.print_exc()
            return str(repr(e))

    return info_msg


def bot_command(command) -> str:
    print(f"{datetime.now()} bot_command", command)

    if command == "/_command_system":
        return system_settings("system")
    elif command == "/_command_system_balance":
        return system_settings("system:balance")
    elif command == "/_command_system_info":
        return system_settings("system:info")
    else:
        return "Неизвестная команда"


def get_messages(chat_id):
    return groups_messages.get(chat_id)


def add_message(chat_id, content):
    messages = groups_messages.get(chat_id)
    messages.append(content)
    messages_length = groups_messages_length.get(chat_id)
    messages_length.append(len(content["content"].split()))
    # if len(messages) % 10 == 0:
    #     messages.append(messages[0])
    #     messages_length.append(len(messages[0]["content"].split()))
    # Максимум 4096 токенов. 1000 токенов - это примерно 750 слов
    while sum(messages_length) >= gpt_chat_settings["max_words_count"] \
            or len(messages) >= gpt_chat_settings["max_messages_count"]:
        del messages[1:3]
        del messages_length[1:3]


@bot.message_handler(content_types=['voice'])
def handle_voice(message):
    chat_id = str(message.chat.id)
    if not check_auth(chat_id):
        err_msg = f"Ваш chat_id:{chat_id} не зарегистрирован"
        bot.reply_to(message, err_msg)
        return

    print_if("voice message:", message)
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_oga = f"{tegram_data_dir_path}/{message.voice.file_unique_id}.oga"
    with open(file_oga, "wb") as ogg:
        ogg.write(downloaded_file)

    text = voice_recognizer.recognize(file_oga)
    print_if("voice recognized text:", text)
    os.remove(file_oga)
    bot.reply_to(message, text)

    response_text = handle(chat_id, text)
    bot.reply_to(message, response_text, parse_mode="Markdown")


@bot.message_handler(content_types=['text'])
def handle_text(message):
    chat_id = str(message.chat.id)

    print_if("text message:", message)

    if not check_auth(chat_id):
        err_msg = f"Ваш chat_id:{chat_id} не зарегистрирован"
        print_if("WARNING UNREGISTERED:", chat_id)
        bot.reply_to(message, err_msg)
        return

    user_text = message.text.strip()

    if chat_id == var.DENIS or chat_id == var.SIA or chat_id == var.FAMILY:
        if user_text.startswith("system"):
            bot.reply_to(message, system_settings(user_text), parse_mode="Markdown")
            return
        if user_text == "/_command_menu":
            keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
            balance_btn = telebot.types.KeyboardButton("1️⃣ Баланс")
            system_btn = telebot.types.KeyboardButton("2️⃣ Список системных команд")
            system_info_btn = telebot.types.KeyboardButton("3️⃣ Системная информация")
            keyboard.add(balance_btn, system_btn, system_info_btn)
            bot.reply_to(message, "Меню добавлено!", reply_markup=keyboard)
            return
        if user_text == "1️⃣ Баланс":
            bot.reply_to(message, bot_command("/_command_system_balance"), parse_mode="Markdown")
            return
        if user_text == "2️⃣ Список системных команд":
            bot.reply_to(message, bot_command("/_command_system"), parse_mode="Markdown")
            return
        if user_text == "3️⃣ Системная информация":
            bot.reply_to(message, bot_command("/_command_system_info"), parse_mode="Markdown")
            return
        if user_text.startswith("/_command"):
            bot.reply_to(message, bot_command(user_text), parse_mode="Markdown")
            return

    if chat_id == var.LK_EGAIS or chat_id == var.TECH or chat_id == var.GPTD77:
        if user_text == "☎️ ВКС":
            bot.reply_to(message, "https://telemost.yandex.ru/j/48927904411584")
            return
        if user_text == "⚙️ Настройки":
            bot.reply_to(message, "Тут пока что нет ничего, но скоро обязательно появится.\nНо это не точно.")
            return

    if not user_text.startswith(telegram_bot_id) \
            and chat_id != var.DENIS and chat_id != var.SIA and chat_id != var.ULIA and chat_id != var.SIA_M:
        add_message(chat_id, {"role": "user", "content": user_text})
        return

    user_text = user_text.replace(telegram_bot_id, "", 1).lstrip()

    response_text = handle(chat_id, user_text)

    bot.reply_to(message, response_text, parse_mode="Markdown")


def handle(chat_id, user_text):
    if user_text.lower().startswith("нарисуй") and (chat_id == var.DENIS or chat_id == var.SIA):
        # Вырезаем слово 'нарисуй', перед отправкой
        return openai.send_to_gpt_image(user_text[7:].lstrip(), gpt_image_settings, print_enable)

    add_message(chat_id, {"role": "user", "content": user_text})
    response_text = openai.send_to_gpt_chat(get_messages(chat_id), gpt_chat_settings, print_enable)
    print_if("response chat text:", response_text)
    add_message(chat_id, {"role": "assistant", "content": response_text})
    return response_text


def start_mi_bot():
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    vks_btn = telebot.types.KeyboardButton("☎️ ВКС")
    settings_btn = telebot.types.KeyboardButton("⚙️ Настройки")
    keyboard.add(vks_btn, settings_btn)
    bot.send_message(var.TECH, "initialization...", reply_markup=keyboard)


def main():
    for group in groups_messages:
        add_message(group, init_role)

    if bot_name == "MI":
        start_mi_bot()

    bot.infinity_polling()


if __name__ == "__main__":
    main()
