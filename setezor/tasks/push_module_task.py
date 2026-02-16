import io
import zipfile
from setezor.tasks.base_job import BaseJob

from setezor.settings import MODULES_PATH


class PushModuleTask(BaseJob):

    @classmethod
    def load_module(cls):
        return True

    def __init__(self, scheduler
                , name: str
                , task_id: str
                , agent_id: str
                , project_id: str
                , module_name: str
                , **kwargs
                ):
        super().__init__(scheduler=scheduler, name=name)
        self.agent_id = agent_id
        self.name = name
        self.project_id = project_id
        self.task_id = task_id
        self.module_name = module_name
        self._coro = self.run()


    async def _task_func(self) -> str:
        # TODO: придумать как избавиться от lazy import
        from setezor.managers import AgentManager
        archive_module = await AgentManager.get_module(agent_id=self.agent_id, module_name=self.module_name)
        if not archive_module:
            return "Failed to get module bytes"
        with zipfile.ZipFile(archive_module) as zf:
            zf.extractall(MODULES_PATH)
        self.loads_all_tasks_for_module(self.module_name)
        return "Module installed"


    @BaseJob.remote_task_notifier
    async def run(self):
        status = await self._task_func()
        return {"status" : status}, ''
