import asyncio
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path


class IpInfoTask(BaseJob):

    module_name = "ip_info"
    IpInfoModule = load_class_from_path(module_name, "executor.py", "IpInfo")

    @classmethod
    def load_module(cls):
        cls.IpInfoModule = load_class_from_path(cls.module_name, "executor.py", "IpInfo")
        return cls.IpInfoModule is not None


    def __init__(self, scheduler, name: str, task_id: int, project_id: str, agent_id: str,
                 target: str, fields: list[str], *args, **kwargs):
        super().__init__(scheduler=scheduler, name=name)
        self.project_id = project_id
        self.task_id = task_id
        self.agent_id = agent_id
        self.target = target
        self.fields = fields

        self._coro = self.run()


    async def _task_func(self) -> dict[str, str]:
        for _ in range(3):
            result = await self.IpInfoModule.get_json(target=self.target, fields=self.fields)
            if (data := result.get("data")):
                return { "raw_result" : data }
            if not result.get("X-Rl"):
                await asyncio.sleep(result.get("X-Ttl", 60) + 1)
        return { "raw_result" : data }


    @BaseJob.remote_task_notifier
    async def run(self):
        data = { "target" : self.target }
        result = await self._task_func()
        data.update(result)
        return data, ''
