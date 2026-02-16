from typing import Optional

import aiohttp
from aiohttp import ClientSession


class ApiClient:

    async def get(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        timeout: int = None,
    ) -> Optional[dict]:
        async with ClientSession() as session:
            async with await session.get(
                url,
                headers=headers,
                params=params,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=False
            ) as resp:
                if resp.status in [200, 201, 204]:
                    return await resp.json()

    async def post(
        self,
        url: str,
        headers: dict = None,
        params: dict = None,
        data: dict = None,
        json: dict = None,
        timeout: int = None,
    ) -> Optional[dict]:
        async with ClientSession() as session:
            async with await session.post(
                url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=aiohttp.ClientTimeout(total=timeout),
                ssl=False
            ) as resp:
                if resp.status in [200, 201, 204]:
                    return await resp.json()