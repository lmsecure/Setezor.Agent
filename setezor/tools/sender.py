from io import BytesIO

import aiohttp
from abc import ABC, abstractmethod

from aiohttp import ClientTimeout

from setezor.logger import logger


class SenderInterface(ABC):

    @classmethod
    @abstractmethod
    async def send_json(cls, url: str, data: dict | list[dict], timeout: float = None):
        pass


class HTTPManager(SenderInterface):
    @classmethod
    async def send_json(cls, url: str, data: dict | list[dict], timeout: float = None, exceptions: bool = True):
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        try:
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.post(url, json=data, ssl=False) as resp:
                    resp_data = await resp.json()
                    if resp.status >= 300:
                        if exceptions:
                            logger.warning(f'Failed to send json | url: {url}, data: {data} | '
                                           f'Response: status code: {resp.status}, resp_data: {resp_data}')
                    else:
                        if exceptions:
                            logger.debug(f'Success to send json | url: {url}, data: {data}')

                    return resp_data, resp.status
        except Exception:
            if exceptions:
                logger.error(f'Failed to send json | url: {url}, data: {data}', exc_info=False)
            return None, 400

    @classmethod
    async def get_bytes(cls, url: str) -> tuple[BytesIO | None, int]:
        buf = BytesIO()
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=15*60)) as session:
            async with session.get(url, ssl=False) as resp:
                if resp.status != 200:
                    return None, resp.status
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    buf.write(chunk)
        buf.seek(0)
        return buf, 200
