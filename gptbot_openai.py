import openai

from gptbot_env import *

openai.api_key = OPENAI_API_KEY


def send_to_gpt_chat(messages, settings, debug=False):
    response = openai.ChatCompletion.create(
        model=settings["model"],
        messages=messages,
        max_tokens=settings["max_tokens"],
        temperature=settings["temperature"],
        top_p=settings["top_p"]
        # frequency_penalty=0,
        # presence_penalty=0
    )
    if debug:
        print("openai response:", response)
    return response.choices[0].message.content


def send_to_gpt_image(message, debug=False):
    response = openai.Image.create(
        prompt=message,
        size="1024x1024"
    )
    if debug:
        print("response image:", response.data[0].url)
    return response.data[0].url
