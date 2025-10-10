from setezor.modules.screenshoter.screenshoter import Screenshoter
from setezor.tasks.base_job import BaseJob


class DNS_A_ScreenshotTask(BaseJob):
    def __init__(
        self, scheduler, name: str, task_id: int, project_id: str,
        agent_id: str, url: str, timeout: float = 20.0
    ):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.url = url
        self.timeout = timeout
        self._coro = self.run()

    async def _task_func(self):
        try:
            raw_result = await Screenshoter.take_screenshot_base64(self.url, self.timeout)
        except Exception as e:
            raise Exception(f"Failed to take screenshot: {e}")
        return {"raw_result": raw_result, "url": self.url}

    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        return result, None
