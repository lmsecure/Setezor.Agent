import asyncio
from typing import Callable

from setezor.logger import logger
from setezor.spy import Spy
from setezor.tools.sender import HTTPManager


class HealthCheck:
    @classmethod
    async def periodic_health_check(cls, event: Callable | None = None):
        is_connect = False
        logger.info('Wait connection...')
        while True:
            for PARENT_URL in Spy.PARENT_AGENT_URLS:
                _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward", data={"sender": Spy.AGENT_ID, "data":""}, exceptions=False)
                if status == 200:
                    if not is_connect:
                        if event:
                            await event()
                        is_connect = True
                        logger.info(f'Successfully connected to {PARENT_URL}')
                    break
            else:
                is_connect = False
            await asyncio.sleep(600 if is_connect else 10)
