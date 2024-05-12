import requests


class ProxyApi:

    def __init__(self, api_key):
        self.api_key = api_key

    def balance(self) -> str:
        api_url = 'https://api.proxyapi.ru/proxyapi/balance'
        response = requests.get(api_url, headers={'Authorization': f'Bearer {self.api_key}'}).json()
        print("balance response:", response)
        return response['balance']
