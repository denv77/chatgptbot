from openai import OpenAI

from var.gptbot_env import *

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_API_URL
)


def send_to_gpt_chat(messages, settings, debug=False):
    response = client.chat.completions.create(
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
    response = client.images.generate(
        # model="dall-e-3",
        prompt=message,
        n=1,
        size="1024x1024"
    )
    if debug:
        print("response image:", response.data[0].url)
    return response.data[0].url
