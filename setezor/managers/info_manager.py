import getpass
from setezor.managers.agent_manager import AgentManager
from setezor.settings import PLATFORM, PYTHON_VERSION, VERSION, PLATFORM_TAG, IMPLEMENTATION, ABI
from setezor.spy import Spy
from setezor.tasks import BaseJob
from setezor.tools.sender import HTTPManager


class InfoManager:
    @classmethod
    async def send_info(cls):
        for PARENT_URL in Spy.PARENT_AGENT_URLS:
            information = AgentManager.generate_data_for_server(
                agent_id=Spy.AGENT_ID,
                data={
                    "signal": "information",
                    "platform": PLATFORM,
                    "platform_tag": PLATFORM_TAG,
                    "implementation": IMPLEMENTATION,
                    "python_version": PYTHON_VERSION,
                    "abi": ABI,
                    "version": VERSION,
                    "tasks": BaseJob.get_available_tasks(),
                    "user": getpass.getuser(),
                    "agent_id": Spy.AGENT_ID,
                }
            )
            _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward", data=information)
            if status == 200:
                break


    @classmethod
    async def send_first_payload_nat(cls):
        return await AgentManager.send_first_payload_nat()