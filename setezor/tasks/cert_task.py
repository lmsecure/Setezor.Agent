import os
from setezor.settings import PATH_PREFIX
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path
from setezor.tools.url_parser import parse_url


class CertTask(BaseJob):

    module_name = "cert"
    CertInfo = load_class_from_path(module_name, "crt4.py", "CertInfo")

    @classmethod
    def load_module(cls):
        cls.CertInfo = load_class_from_path(cls.module_name, "crt4.py", "CertInfo")
        return cls.CertInfo is not None

    def __init__(self, scheduler, name: str, task_id: int, target: str, port: int, agent_id: int, project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.target = target
        self.port = port
        self.data = parse_url(f"https://{self.target}:{self.port}/")
        self.agent_id = agent_id
        self.project_id = project_id
        self._coro = self.run()

    async def _task_func(self):
        return self.CertInfo.get_cert_and_parse(resource=self.data)

  
    @BaseJob.remote_task_notifier
    async def run(self):
        raw_result = await self._task_func()
        data = {"raw_result": raw_result, "data": self.data}
        return data, "pem"