from typing import Any
from setezor.tasks.base_job import BaseJob
from setezor.tools.ip_tools import get_interfaces


class SelfHostedAgentInterfaces(BaseJob):

    def __init__(self, scheduler, name: str, task_id: int, project_id: str, agent_id: str, object_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.project_id = project_id
        self.task_id = task_id
        self.agent_id = agent_id
        self.object_id = object_id
        self._coro = self.run()

    async def _task_func(self) -> list[Any]:
        return [iface.model_dump() for iface in get_interfaces() if iface.ip]

    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        data = {
            "raw_result": result,
            "object_id": self.object_id
        }
        return data, ''
