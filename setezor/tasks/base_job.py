import asyncio
from abc import abstractmethod

from aiojobs._job import Job

from setezor.schemas.task import TaskStatus
from setezor.logger import logger


class BaseJob(Job):

    module_name = ""
    description = ""
    payload: dict = {}

    def __init__(self, scheduler, name: str, update_graph: bool = True, agent_id: int | None = None):
        super().__init__(None, scheduler)  # FixMe add custom exception handler
        self.agent_id = agent_id
        self.name = name
        self.update_graph = update_graph

    @classmethod
    def load_module(cls):
        raise NotImplementedError

    @abstractmethod
    async def run(self, *args, **kwargs):
        pass

    @logger.not_implemented
    async def soft_stop(self):
        pass

    @logger.not_implemented
    async def hard_stop(self):
        pass

    async def get_status(self):
        return {
            self.active(): 'active',
            self.pending(): 'pending',
            self.closed(): 'finished'
        }[True]

    @logger.not_implemented
    async def get_progress(self):
        pass

    async def close(self, *, timeout=None):
        return await super().close(timeout=timeout)


    @staticmethod
    def remote_task_notifier(func):
        async def wrapped(self, *args, **kwargs):
            task_id = self.task_id
            agent_id = self.agent_id
            task_status_data = {
                "signal": "task_status",
                "task_id": task_id,
                "status": TaskStatus.started,
                "type": "success",
                "traceback": ""
            }
            await self._scheduler.notify(agent_id=agent_id,   # меняем инфу по статусу задачи на сервере
                                         data=task_status_data)
            logger.debug(f"STARTED TASK {func.__qualname__}")
            try:
                result, raw_result_extension = await func(self, *args, **kwargs)
            except Exception as e:
                task_status_data["status"] = TaskStatus.failed
                task_status_data["traceback"] = str(e)
                task_status_data["type"] = "error"

                await self._scheduler.notify(agent_id=agent_id,   # меняем инфу по статусу задачи на сервере
                                             data=task_status_data)
                logger.error(f"TASK {func.__qualname__} FAILED")
                return
            await self._scheduler.give_result_to_task_manager(
                task_id=task_id,
                agent_id=agent_id,
                result=result,
                raw_result_extension=raw_result_extension
            )
            return result
        return wrapped

    async def _close(self, timeout):
        return await super()._close(timeout)

    def _done_callback(self, task):
        scheduler = self._scheduler
        scheduler._done(self)
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            pass
        else:
            if exc is not None and not self._explicit:
                self._report_exception(exc)
                scheduler._failed_tasks.put_nowait(task)
            else:
                ...
        self._scheduler = None
        self._closed = True


    @classmethod
    def get_task_by_class_name(cls, name: str):
        for model_class in BaseJob.__subclasses__():
            if model_class.__name__ == name:
                return model_class
        return None


    @classmethod
    def get_available_tasks(cls):
        result = {}
        for task in BaseJob.__subclasses__():
            result.update(
                {task.__name__ : {
                    "module_name" : task.module_name,
                    "module_is_installed" : task.load_module(),
                    "description" : task.description,
                    "payload": task.payload,
                    }
                }
            )
        return result


    @classmethod
    def loads_all_tasks_for_module(cls, module_name: str):
        for task in BaseJob.__subclasses__():
            if task.module_name == module_name:
                task.load_module()