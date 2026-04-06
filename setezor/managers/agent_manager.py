import asyncio
import base64
import io
from io import BytesIO

import orjson
from fastapi.responses import StreamingResponse

from setezor.tools.sender import HTTPManager
from setezor.spy import Spy
from setezor.tools.ip_tools import get_interfaces
from setezor.managers.cipher_manager import Cryptor


class AgentManager:
    @classmethod
    def single_cipher(cls, key: str, is_connected: bool, data: dict):
        initial_data = orjson.dumps(data)
        if not is_connected:
            return base64.b64encode(initial_data)
        return base64.b64encode(Cryptor.encrypt(initial_data, key))

    @classmethod
    def generate_data_for_server(cls, agent_id: str, data: dict):
        ciphered_payload_by_current_agent = cls.single_cipher(key=Spy.SECRET_KEY,
                                                              is_connected=True,
                                                              data=data)
        return {
            "sender": agent_id,
            "data": ciphered_payload_by_current_agent.decode()
        }


    @classmethod
    def interfaces(cls):
        interfaces = [iface.model_dump() for iface in get_interfaces() if iface.ip]
        initial_data = orjson.dumps(interfaces)
        return {"data": base64.b64encode(Cryptor.encrypt(initial_data, Spy.SECRET_KEY))}

    @classmethod
    async def send_to_parent(cls, data: dict, keep_connection: bool = False):
        for url in Spy.PARENT_AGENT_URLS:
            data, status = await HTTPManager.send_json(url=f"{url}/api/v1/agents/backward{"?keep_connection=true" if keep_connection else ""}", data=data)
            if status == 200:
                return data

    @classmethod
    async def get_module(cls, agent_id: str, module_name: str) -> BytesIO | None:
        for url in Spy.PARENT_AGENT_URLS:
            data, status = await HTTPManager.get_bytes(
                url=f"{url}/api/v1/agents/get_module/{agent_id}/{module_name}")
            if status == 200:
                return data


    @classmethod
    async def send_first_payload_nat(cls):
        retries = 3
        while retries:
            if Spy.is_connect:
                connection_request = AgentManager.generate_data_for_server(agent_id=Spy.AGENT_ID, data={"signal": "check_connection", "agent_id": Spy.AGENT_ID})
                is_connected = False
                for pagent in Spy.PARENT_AGENT_URLS:
                    data, status = await HTTPManager.send_json(f"{pagent}/api/v1/agents/backward?keep_connection=true", data=connection_request)
                    if status != 200 or (not data):
                        await asyncio.sleep(5)
                        continue
                    payload = data.get("data")
                    b64decoded = base64.b64decode(payload)
                    deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                                        key=Spy.SECRET_KEY)
                    connection_payload = orjson.loads(deciphered_payload)
                    if connection_payload.get("is_connected"):
                        is_connected = True
                        break
                if is_connected:
                    break
                retries -= 1
            await asyncio.sleep(1)
        if not is_connected:
            raise Exception("I'm not connected")