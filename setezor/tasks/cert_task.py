from setezor.tasks.base_job import BaseJob
from setezor.modules.osint.cert.crt4 import CertInfo
from setezor.tools.url_parser import parse_url


class CertTask(BaseJob):


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
        return CertInfo.get_cert_and_parse(resource=self.data)

  
    @BaseJob.remote_task_notifier
    async def run(self):
        raw_result = await self._task_func()
        data = {"raw_result": raw_result, "data": self.data}
        return data, "pem"