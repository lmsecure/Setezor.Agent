import asyncio
import json
import orjson
import base64
from setezor.managers.cipher_manager import Cryptor
from setezor.schemas.task import TaskPayload
from .task_manager import TaskManager
from .agent_manager import AgentManager
from setezor.tools.sender import HTTPManager
from setezor.spy import Spy

class TaskCrawlerManager:
    @Spy.task_listener
    @staticmethod
    async def get_tasks():
        if not Spy.SECRET_KEY:
            return
        INIT_TIME_TO_SLEEP: float = 10.0
        TIME_TO_SLEEP: float = INIT_TIME_TO_SLEEP
        MAX_TIME: float = 600.0
        tasks_request = AgentManager.generate_data_for_server(agent_id=Spy.AGENT_ID, data={"signal": "agent_tasks", "agent_id": Spy.AGENT_ID})
        tasks_request_for_soft_stop = AgentManager.generate_data_for_server(agent_id=Spy.AGENT_ID, data={"signal": "agent_tasks_to_soft_stop", "agent_id": Spy.AGENT_ID})
        tasks_request_for_cancel = AgentManager.generate_data_for_server(agent_id=Spy.AGENT_ID, data={"signal": "agent_tasks_to_cancel", "agent_id": Spy.AGENT_ID})
        
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
        if not is_connected:
            raise Exception("I'm not connected")
        
        while True:
            for pagent in Spy.PARENT_AGENT_URLS:
                data, status = await HTTPManager.send_json(f"{pagent}/api/v1/agents/backward?keep_connection=true", data=tasks_request)
                if status != 200 or (not data):
                    continue
                payload = data.get("data")
                b64decoded = base64.b64decode(payload)
                deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                                    key=Spy.SECRET_KEY)
                tasks_list = orjson.loads(deciphered_payload)
                for task in tasks_list:
                    task_params = json.loads(task.get("params"))
                    task_payload = TaskPayload(
                                    task_id=task.get("id"),
                                    project_id=task.get("project_id"),
                                    agent_id=task.get("agent_id"),
                                    job_params=task_params,
                                    job_name=task.get("created_by"))
                    await TaskManager.create_job_on_agent("create_job", task_payload)
                
                tasks_to_soft_stop, status = await HTTPManager.send_json(f"{pagent}/api/v1/agents/backward?keep_connection=true", data=tasks_request_for_soft_stop)
                payload = tasks_to_soft_stop.get("data")
                b64decoded = base64.b64decode(payload)
                deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                                     key=Spy.SECRET_KEY)
                tasks_list_to_soft_stop = orjson.loads(deciphered_payload)
                for task in tasks_list_to_soft_stop:
                    await TaskManager.soft_stop_task_on_agent(id=task["id"])

                tasks_to_cancel, status = await HTTPManager.send_json(f"{pagent}/api/v1/agents/backward?keep_connection=true", data=tasks_request_for_cancel)
                payload = tasks_to_cancel.get("data")
                b64decoded = base64.b64decode(payload)
                deciphered_payload = Cryptor.decrypt(data=b64decoded,
                                                     key=Spy.SECRET_KEY)
                tasks_list_to_cancel = orjson.loads(deciphered_payload)
                for task in tasks_list_to_cancel:
                    await TaskManager.cancel_task_on_agent(id=task["id"])

                
                if not TaskManager.get_total_count_of_tasks():
                    TIME_TO_SLEEP = min(MAX_TIME, TIME_TO_SLEEP * 1.25)
                else:
                    TIME_TO_SLEEP = INIT_TIME_TO_SLEEP
                break
            await asyncio.sleep(TIME_TO_SLEEP)