import asyncio
import base64

import aiohttp
import orjson

from setezor.clients.base_client import ApiClient
from setezor.managers import Cryptor
from setezor.settings import current_port
from setezor.spy import Spy


class CliManager:

    def __init__(self, api_client: ApiClient):
        self.api_client = api_client

    def refresh_agent(self):
        payload = orjson.dumps({'signal': 'refresh_agent'})
        Spy.from_file()
        data = {
            'sender': Spy.AGENT_ID,
            'data': base64.b64encode(Cryptor.encrypt(payload, Spy.SECRET_KEY)).decode()
        }
        try:
            asyncio.run(self.api_client.post(
                    url=f'https://0.0.0.0:{current_port}/api/v1/agents/forward',
                    json=data,
                )
            )
        except aiohttp.client_exceptions.ServerDisconnectedError:
            pass
        except aiohttp.client_exceptions.ClientConnectorError:
            Spy.remove_config()