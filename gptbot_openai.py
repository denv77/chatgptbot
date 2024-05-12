from openai import OpenAI


class GptBotOpenAI:

    def __init__(self, api_key, api_url):
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_url
        )

    def send_to_gpt_chat(self, messages, settings, debug=False):
        response = self.client.chat.completions.create(
            model=settings["model"],
            messages=messages,
            max_tokens=settings["max_tokens"],
            temperature=settings["temperature"],
            top_p=settings["top_p"]
            # frequency_penalty=0,
            # presence_penalty=0
        )
        if debug:
            print("[DEBUG] openai chat response:", response)
        return response.choices[0].message.content

    def send_to_gpt_image(self, prompt, settings, debug=False):
        response = self.client.images.generate(
            model=settings["model"],
            prompt=prompt,
            size=settings["size"],
            n=1
        )
        if debug:
            print("[DEBUG] openai image response:", response)
        return response.data[0].url
