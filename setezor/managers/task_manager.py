import os
import base64
from fastapi import BackgroundTasks
import aiofiles
import orjson
from setezor.managers.scheduler_manager import SchedulerManager
from setezor.tasks.base_job import BaseJob
from setezor.schemas.task import TaskPayload, \
    TaskStatus
from setezor.tasks import get_task_by_class_name
from setezor.spy import Spy
from setezor.managers.agent_manager import AgentManager
from setezor.managers.sender_manager import HTTPManager
from setezor.managers.cipher_manager import Cryptor
from setezor.schemas.agent import BackWardData
from setezor.settings import PATH_PREFIX
from setezor.interfaces.observer import Observer
from setezor.logger import logger


class TaskManager(Observer):

    schedulers = {}
    tasks = {}

    @classmethod  # метод агента на создание джобы
    async def create_job_on_agent(cls, payload: TaskPayload):
        job_cls = get_task_by_class_name(payload.job_name)
        scheduler = cls.create_new_scheduler(job_cls)
        task_id = payload.task_id
        if task_id in cls.tasks:
            return None
        project_id = payload.project_id
        new_job: BaseJob = job_cls(
            name=f"Task {task_id}",
            scheduler=scheduler,
            task_id=task_id,
            project_id=project_id,
            **payload.job_params
        )
        job: BaseJob = await scheduler.spawn_job(new_job)
        cls.tasks[task_id] = job
        return task_id


    @classmethod  # метод агента на мягкое завершение таски
    async def soft_stop_task_on_agent(cls, id: str) -> str:
        task = cls.tasks.get(id)
        await task.soft_stop()
        return id

    @classmethod  # метод агента на создание шедулера
    def create_new_scheduler(cls, job: BaseJob):
        if job in cls.schedulers:
            return cls.schedulers[job]
        new_scheduler = SchedulerManager.for_job(job=job)
        cls.schedulers[job] = new_scheduler
        new_scheduler.attach(cls)
        return new_scheduler

    @Spy.spy_func(method="POST", endpoint="/api/v1/agents/forward")
    @staticmethod  # метод агента на отправку сигнала следующему звену
    async def forward_request(
        payload: dict,
        background_tasks: BackgroundTasks = None
    ) -> dict:
        data: bytes = base64.b64decode(payload["data"])
        if not Spy.SECRET_KEY:
            try:
                connection_data = data.decode()
                connection_payload = orjson.loads(connection_data)
                if not connection_payload.pop("signal", None) == "connect":
                    raise Exception("Invalid packet")
                Spy.SECRET_KEY = connection_payload.get("key")
                Spy.PARENT_AGENT_URLS = connection_payload.get("parent_agents_urls")
                Spy.AGENT_ID = connection_payload.get("agent_id")
                async with aiofiles.open(os.path.join(PATH_PREFIX, "config.json"), 'w') as file:
                    await file.write(orjson.dumps(connection_payload).decode())
                return {"status": "OK"}
            except Exception as e:
                logger.error(str(e))
                return {"status": "You are suspicious"}
        try:
            deciphered_data: bytes = Cryptor.decrypt(
                data=data, key=Spy.SECRET_KEY)
        except Exception as e:
            logger.error(str(e))
            return {}

        json_data: dict = orjson.loads(deciphered_data)
        close_connection = json_data.get("close_connection")
        if url := json_data.get("next_agent_url"):  # если мы посредник
            if close_connection:
                background_tasks.add_task(HTTPManager.send_json,
                                          url=url,
                                          data=json_data['data'])
                logger.debug(f"Redirected payload to {url}")
                return {}
            else:
                logger.debug(f"Redirected payload to {url}")
                data, status = await HTTPManager.send_json(url=url, data=json_data['data'])
                return data

        signal = json_data.pop("signal", None)
        match signal:
            case "interfaces":
                return AgentManager.interfaces()
            case "create_task":
                payload = TaskPayload(**json_data)
                await TaskManager.create_job_on_agent(payload=payload)
                return {}
            case "soft_stop_task":
                task_id = json_data.get("id")
                await TaskManager.soft_stop_task_on_agent(id=task_id)
                return {}
            case _:
                return {}

    @Spy.spy_func(method="POST", endpoint="/api/v1/agents/backward")
    @staticmethod  # метод агента на отправку данных родителю
    async def backward_request(
        data: BackWardData,
        background_tasks: BackgroundTasks = None,
        keep_connection: bool = False,
    ) -> bool:
        if keep_connection:
            return await AgentManager.send_to_parent(data=data.model_dump(), 
                                                     keep_connection=keep_connection)
        background_tasks.add_task(AgentManager.send_to_parent,
                                  data=data.model_dump())
        return True

    @classmethod
    async def send_result_to_parent_agent(cls,
                                          agent_id: str,
                                          task_id: str,
                                          task_data: dict,
                                          raw_result_extension: str = ''):
        result = {
            "signal": "result_entities",
            "task_id": task_id,
            "result": task_data,
            "raw_result_extension": raw_result_extension,
        }
        ciphered_data = AgentManager.single_cipher(is_connected=True,
            key=Spy.SECRET_KEY, data=result).decode()
        data_for_parent_agent = {
            "sender": agent_id,
            "data": ciphered_data
        }
        for PARENT_URL in Spy.PARENT_AGENT_URLS:
            _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward",
                                        data=data_for_parent_agent)
            if status == 200:
                break
        cls.delete_task(task_id=task_id)

    @classmethod
    async def notify(cls, agent_id: str, data: dict):
        data_for_server = AgentManager.generate_data_for_server(agent_id=agent_id,
                                                                data=data)
        for PARENT_URL in Spy.PARENT_AGENT_URLS:
            _, status = await HTTPManager.send_json(url=f"{PARENT_URL}/api/v1/agents/backward",
                                        data=data_for_server)
            if status == 200:
                break
        if data.get("signal") == "task_status" and data.get("status") == TaskStatus.failed:
            cls.delete_task(task_id=data.get("task_id"))


    @classmethod
    def get_total_count_of_tasks(cls):
        return sum([len(sch) for sch in cls.schedulers.values()])
    
    @classmethod
    def delete_task(cls, task_id: str):
        cls.tasks.pop(task_id, None)