import asyncio
import aiohttp
import platform
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from setezor.settings import PLATFORM


class SenderInterface(ABC):
    @abstractmethod
    async def send_json(cls, url: str, data: dict | list[dict]):
        pass


class HTTPManager(SenderInterface):
    _executor = ThreadPoolExecutor(max_workers=1)

    @classmethod
    async def send_json(cls, url: str, data: dict | list[dict]):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            cls._executor,
            lambda: cls._run_in_selector_loop(url, data)
        )

    @classmethod
    def _run_in_selector_loop(cls, url: str, data: dict | list[dict]):
        if PLATFORM == "Windows":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(cls._send(url, data))

    @classmethod
    async def _send(cls, url: str, data: dict | list[dict]):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=data, ssl=False) as resp:
                    return await resp.json(), resp.status
            except (aiohttp.ClientConnectorError,
                    aiohttp.ConnectionTimeoutError,
                    aiohttp.ContentTypeError,
                    aiohttp.InvalidURL):
                return None, 400
