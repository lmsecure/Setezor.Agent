import base64

from setezor.settings import get_platform_name
from setezor.tasks import BaseJob
from setezor.tools.importer import add_permissions, load_class_from_path


class ParseSiteTask(BaseJob):

    module_name = 'site_parser'
    description = ''
    payload: dict = {'platform_name': get_platform_name()}
    SiteParser = load_class_from_path(module_name, "parser.py", "SiteParser")

    @classmethod
    def load_module(cls):
        cls.SiteParser = load_class_from_path(cls.module_name, "parser.py", "SiteParser")
        if not cls.SiteParser:
            return False
        add_permissions(cls.module_name, "external", "playwright", "driver", "node")
        add_permissions(cls.module_name, "browser", "chrome")
        add_permissions(cls.module_name, "browser", "chrome_crashpad_handler")
        return True

    def __init__(
        self, scheduler, name: str, task_id: int, project_id: str,
        agent_id: str, url: str, with_screenshot: bool, with_wappalyzer: bool, timeout: float = 50.0
    ):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.url = url
        self.with_screenshot = with_screenshot
        self.timeout = timeout * 1000
        self.with_wappalyzer = with_wappalyzer
        self._coro = self.run()

    async def _task_func(self):
        try:
            result = await self.SiteParser.parse(
                self.task_id, self.url, self.with_screenshot, self.with_wappalyzer, self.timeout
            )
        except Exception as e:
            raise Exception(f"Failed to create web archive: {e}")
        return {
            "har": base64.b64encode(result['har']).decode(),
            "screenshot": base64.b64encode(result['screenshot']).decode() if result['screenshot'] else None,
            "wappalyzer_data": result['wappalyzer_data'],
            "url": self.url,
            "raw_result": ""
        }

    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        return result, None
