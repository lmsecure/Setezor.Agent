import traceback
from time import time
from setezor.tools.importer import load_class_from_path
from .base_job import BaseJob


class RdapTask(BaseJob):

    module_name = "rdap"
    Rdap = load_class_from_path(module_name, "rdap.py", "Rdap")

    @classmethod
    def load_module(cls):
        cls.Rdap = load_class_from_path(cls.module_name, "rdap.py", "Rdap")
        return cls.Rdap is not None

    def __init__(self, scheduler, name: str, task_id: int, target: str, agent_id: int, project_id: str):
        super().__init__(scheduler = scheduler, name = name)
        self.task_id = task_id
        self.target = target
        self.project_id = project_id
        self.agent_id = agent_id
        self._coro = self.run()


    async def _task_func(self):
        return await self.Rdap.get_rdap_raw(target=self.target)


    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        data = {
            "raw_result": result,
            "target": self.target,
        }
        return data, 'json'
