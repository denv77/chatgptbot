import json
import sys
import traceback
from typing import Any

import telebot
import yaml

from gptbot_init_roles import *
from gptbot_openai import *
from gptbot_voice_recognizer import *

groups_messages = {
    FAMILY: [],
    ULIA: [],
    GPTD77: [],
    DENIS: [],
    SIA: [],
    LK_EGAIS: []
}

groups_messages_length = {
    FAMILY: [],
    ULIA: [],
    GPTD77: [],
    DENIS: [],
    SIA: [],
    LK_EGAIS: []
}

groups_names = {
    "FAMILY": FAMILY,
    "SIA": SIA,
    "ULIA": ULIA,
    "GPTD77": GPTD77,
    "DENIS": DENIS,
    "LK_EGAIS": LK_EGAIS
}

print("starting...")

base_dir = os.path.dirname(os.path.realpath(__file__))
tegram_data_dir = f"{base_dir}/data"
os.makedirs(tegram_data_dir, exist_ok=True)
print("base_dir:", base_dir)
print("tegram_data_dir:", tegram_data_dir)
print("sys.path[0]:", sys.path[0])

with open(f"{base_dir}/config.yaml", "r") as f:
    config = yaml.safe_load(f)

print(f"config: {json.dumps(config, indent=4)}")
gpt_chat_settings = config["gpt_chat_settings"]
print_enable = config["app_settings"]["print_enable"]
bot_name = config["app_settings"]["bot_name"]

if bot_name == "DV":
    telegram_api_key = TELEGRAM_API_KEY_DV
    telegram_bot_id = "@denv77Bot"
    init_role = init_role_denis
elif bot_name == "SIA":
    telegram_api_key = TELEGRAM_API_KEY_SIA
    telegram_bot_id = "@AmigoSiaBot"
    init_role = init_role_sia
elif bot_name == "MI":
    telegram_api_key = TELEGRAM_API_KEY_MI
    telegram_bot_id = "@MihalIvanichBot"
    init_role = init_role_lk_egais
elif bot_name == "A":
    telegram_api_key = TELEGRAM_API_KEY_A
    telegram_bot_id = "@Afanasiy77Bot"
    init_role = init_role_family
else:
    raise Exception(f"bot_name: {bot_name}")

bot = telebot.TeleBot(telegram_api_key)

print(f"bot: {json.dumps(bot.get_me().to_dict(), indent=4)}")


def check_auth(chat_id):
    messages = groups_messages.get(chat_id)
    return messages is not None


def print_if(*args: Any):
    if print_enable:
        print(*args)


def system_settings(settings_str):
    print(settings_str)

    msg = settings_str.split(":", 2)

    info_msg = "system:\ninfo\n[reset|hard_reset]:GROUP_NAME\nsettings:{}\nadd:{name,role:[system|user|assistant],content}"
    if settings_str == "system" or len(msg) < 2:
        return info_msg

    if msg[1] == "info":
        all_counts = {}
        for name in groups_names:
            all_counts[name] = f'size: {len(groups_messages.get(groups_names.get(name)))} ' \
                               f'words: {sum(groups_messages_length.get(groups_names.get(name)))}'
        return f'{gpt_chat_settings}\n\n{groups_names}\n\n{all_counts}\n\n{init_role}'

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

    if msg[1] == "settings":
        try:
            settings = json.loads(msg[2])
            for k in settings:
                gpt_chat_settings[k] = settings[k]
                config["gpt_chat_settings"] = gpt_chat_settings
            with open(f"{base_dir}/config.yaml", "w") as cfg_file:
                yaml.dump(config, cfg_file)
            return f'{gpt_chat_settings}'
        except Exception as e:
            traceback.print_exc()
            return str(repr(e))

    return info_msg


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
        return f"Ваш chat_id:{chat_id} не зарегистрирован"

    print_if("voice message:", message)
    file_info = bot.get_file(message.voice.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    file_oga = f"{tegram_data_dir}/{message.voice.file_unique_id}.oga"
    with open(file_oga, "wb") as ogg:
        ogg.write(downloaded_file)

    text = recognize_voice(file_oga)
    print_if("voice recognized text:", text)
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

    if (chat_id == DENIS or chat_id == SIA or chat_id == FAMILY) and user_text.startswith("system"):
        bot.reply_to(message, system_settings(user_text))
        return

    if not user_text.startswith(telegram_bot_id) and chat_id != DENIS and chat_id != SIA and chat_id != ULIA:
        add_message(chat_id, {"role": "user", "content": user_text})
        return

    user_text = user_text.replace(telegram_bot_id, "", 1).lstrip()

    response_text = handle(chat_id, user_text)

    bot.reply_to(message, response_text)


def handle(chat_id, user_text):
    if user_text.lower().startswith("нарисуй"):
        return send_to_gpt_image(user_text, print_enable)

    add_message(chat_id, {"role": "user", "content": user_text})
    response_text = send_to_gpt_chat(get_messages(chat_id), gpt_chat_settings, print_enable)
    print_if("response chat text:", response_text)
    add_message(chat_id, {"role": "assistant", "content": response_text})
    return response_text


def main():
    for group in groups_messages:
        add_message(group, init_role)

    bot.infinity_polling()


if __name__ == "__main__":
    main()
