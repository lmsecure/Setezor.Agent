import asyncio
import io
import os
import base64
import sys

from fastapi import BackgroundTasks
import aiofiles
import orjson
from starlette.responses import StreamingResponse

from setezor.managers.health_check_manager import HealthCheck
from setezor.managers.info_manager import InfoManager
from setezor.managers.scheduler_manager import SchedulerManager
from setezor.tasks.base_job import BaseJob
from setezor.schemas.task import TaskPayload, \
    TaskStatus
from setezor.spy import Spy
from setezor.managers.agent_manager import AgentManager
from setezor.tools.sender import HTTPManager
from setezor.managers.cipher_manager import Cryptor
from setezor.schemas.agent import BackWardData
from setezor.settings import PATH_PREFIX
from setezor.interfaces.observer import Observer
from setezor.logger import logger


class TaskManager(Observer):

    schedulers = {}
    tasks = {}

    @classmethod  # метод агента на создание джобы
    async def create_job_on_agent(cls, signal: str, payload: TaskPayload):
        back_signal = "task_status" if signal == "create_task" else "job_status"
        job_cls = BaseJob.get_task_by_class_name(payload.job_name)
        scheduler = cls.create_new_scheduler(job_cls)
        task_id = payload.task_id
        if task_id in cls.tasks:
            return None
        project_id = payload.project_id
        try:
            new_job: BaseJob = job_cls(
                name=f"Task {task_id}",
                scheduler=scheduler,
                task_id=task_id,
                project_id=project_id,
                **payload.job_params
            )
        except Exception:
            task_status_data = {
            "signal": back_signal,
            "task_id": task_id,
            "status": TaskStatus.failed,
            "type": "error",
            "traceback": "Failed to create task on agent"
            }
            await cls.notify(agent_id=payload.agent_id, data=task_status_data)
            logger.error(f'Failed to create task | task_id: {task_id}, payload: {payload}')
            return
        task_status_data = {
            "signal": back_signal,
            "task_id": task_id,
            "status": TaskStatus.registered,
            "type": "success",
            "traceback": ""
        }
        await cls.notify(agent_id=payload.agent_id, data=task_status_data)
        job: BaseJob = await scheduler.spawn_job(new_job)
        logger.info(f'Created task | task_id: {task_id}, payload: {payload}')
        cls.tasks[task_id] = job
        return task_id

    @classmethod  # метод агента на мягкое завершение таски
    async def soft_stop_task_on_agent(cls, id: str) -> str:
        task = cls.tasks.get(id)
        if task:
            await task.soft_stop()
            task_status_data = {
                "signal": "task_status",
                "task_id": id,
                "status": TaskStatus.stopped,
                "type": "warning",
                "traceback": ""
            }
            await cls.notify(
                agent_id=task.agent_id,
                data=task_status_data
            )
            logger.info(f'Stopped task | task_id: {id}')
        return id
    
    @classmethod  # метод агента на дроп таски
    async def cancel_task_on_agent(cls, id: str) -> str:
        task = cls.tasks.get(id)
        if task:
            await task.close()
            task_status_data = {
                "signal": "task_status",
                "task_id": id,
                "status": TaskStatus.canceled,
                "type": "warning",
                "traceback": ""
            }
            await cls.notify(
                agent_id=task.agent_id,
                data=task_status_data
            )
            logger.info(f'Canceled task | task_id: {id}')
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
                loop = asyncio.get_running_loop()
                loop.create_task(HealthCheck.periodic_health_check(event=InfoManager.send_info))
                return {"status": "OK"}
            except Exception:
                logger.error(f'Error on forward_request | payload: {payload}')
                return {"status": "You are suspicious"}
        try:
            deciphered_data: bytes = Cryptor.decrypt(
                data=data, key=Spy.SECRET_KEY)
        except Exception as exp:
            logger.error(f'Error while decrypting data: {str(exp)}', exc_info=False)
            return {}

        json_data: dict = orjson.loads(deciphered_data)
        close_connection = json_data.get("close_connection")
        if url := json_data.get("next_agent_url"):  # если мы посредник
            if close_connection:
                background_tasks.add_task(HTTPManager.send_json,
                                          url=url,
                                          data=json_data)
                data = {}
            else:
                data, status = await HTTPManager.send_json(url=url, data=json_data)
            logger.debug(f"Redirected payload to {url}")
            return data

        signal = json_data.pop("signal", None)
        match signal:
            case "interfaces":
                return AgentManager.interfaces()
            case "create_job" | "create_task":
                payload = TaskPayload(**json_data)
                await TaskManager.create_job_on_agent(signal=signal, payload=payload)
                return {}
            case "soft_stop_task":
                task_id = json_data.get("id")
                await TaskManager.soft_stop_task_on_agent(id=task_id)
                return {}
            case "cancel_task":
                task_id = json_data.get("id")
                await TaskManager.cancel_task_on_agent(id=task_id)
                return {}
            case "refresh_agent":
                Spy.remove_config()
                os.execv(sys.executable, [sys.executable, *sys.argv])
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
                logger.info(f'FINISHED TASK {task_id}')
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

    @staticmethod
    def _stream_bytes(buf: io.BytesIO, chunk_size=1024 * 1024):
        buf.seek(0)
        while chunk := buf.read(chunk_size):
            yield chunk

    @Spy.spy_func(method="GET", endpoint="/api/v1/agents/get_module/{agent_id}/{module_name}")
    @staticmethod
    async def get_module(module_name: str, agent_id: str) -> StreamingResponse:
        data = await AgentManager.get_module(module_name=module_name, agent_id=agent_id)
        return StreamingResponse(
            TaskManager._stream_bytes(data),
            media_type="application/octet-stream"
        )
