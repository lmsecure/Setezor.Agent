import os
from typing import Any
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path

class DNSTask(BaseJob):

    module_name = "dns_info"
    DNSModule = load_class_from_path(module_name, "dns_info.py", "DNS")

    @classmethod
    def load_module(cls):
        cls.DNSModule = load_class_from_path(cls.module_name, "dns_info.py", "DNS")
        return cls.DNSModule is not None

    def __init__(self, scheduler, name: str, task_id: int, project_id: str, agent_id: str,
                 domain: str, ns_servers: list[str] | None = None, records: list[str] | None = None):
        super().__init__(scheduler=scheduler, name=name)
        self.project_id = project_id
        self.task_id = task_id
        self.agent_id = agent_id
        self.target = domain
        self.ns_servers = ns_servers
        self.records = records
        self._coro = self.run()

    async def _task_func(self) -> list[Any]:
        return await self.DNSModule.query(target = self.target, ns_servers=self.ns_servers, records=self.records)

    @BaseJob.remote_task_notifier
    async def run(self):
        data = await self._task_func()
        return data, 'json'
