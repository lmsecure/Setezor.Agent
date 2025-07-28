import asyncio
from setezor.spy import Spy
from setezor.tools.sender import HTTPManager


class HealthCheck:
    @classmethod
    async def periodic_health_check(cls):
        while True:
            for PARENT_URL in Spy.PARENT_AGENT_URLS:
                _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward", data={"sender": Spy.AGENT_ID, "data":""})
                if status == 200:
                    break
            await asyncio.sleep(600)