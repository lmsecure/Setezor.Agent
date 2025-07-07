import asyncio
from setezor.tools.sender import HTTPManager


class HealthCheck:
    @classmethod
    async def periodic_health_check(cls, agent_id: str, parent_agent_urls: list[str]):
        while True:
            for PARENT_URL in parent_agent_urls:
                _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward", data={"sender": agent_id, "data":""})
                if status == 200:
                    break
            await asyncio.sleep(600)