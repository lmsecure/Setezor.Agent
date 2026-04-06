import asyncio
from typing import Callable

from setezor.logger import logger
from setezor.spy import Spy
from setezor.tools.sender import HTTPManager


class HealthCheck:
    @classmethod
    async def periodic_health_check(cls, event: Callable | None = None):
        logger.info('Wait connection...')
        while True:
            Spy.health_check_delay_accumulate += 1
            if Spy.health_check_delay_accumulate < Spy.health_check_delay:
                await asyncio.sleep(1)
                continue
            Spy.health_check_delay_accumulate = 0
            logger.debug('send check connect')

            for PARENT_URL in Spy.PARENT_AGENT_URLS:
                _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward", data={"sender": Spy.AGENT_ID, "data":""}, exceptions=False)
                if status == 200:
                    if not Spy.is_connect:
                        if event:
                            await event()
                        Spy.is_connect = True
                        Spy.health_check_delay = 600
                        logger.info(f'Successfully connected to {PARENT_URL}')
                    break
            else:
                Spy.is_connect = False
