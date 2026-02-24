import json
import os
import traceback
from time import time
import asyncio
import itertools
from setezor.settings import PATH_PREFIX
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path


class SdFindTask(BaseJob):

    module_name = "sd_search"
    Domain_brute = load_class_from_path(module_name, "domain_brute.py", "Domain_brute")
    CrtSh = load_class_from_path(module_name, "crtsh.py", "CrtSh")

    @classmethod
    def load_module(cls):
        cls.Domain_brute = load_class_from_path(cls.module_name, "domain_brute.py", "Domain_brute")
        cls.CrtSh = load_class_from_path(cls.module_name, "crtsh.py", "CrtSh")
        return (cls.Domain_brute is not None) and (cls.CrtSh is not None)


    def __init__(self, scheduler, name: str, task_id: int, domain: str, project_id: str, crt_sh: bool, agent_id: str, dict_file: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.domain = domain
        self.dict_file = dict_file
        self.crt_sh = crt_sh
        self.agent_id = agent_id
        self._coro = self.run()


    async def _task_func(self) -> list[dict]:
        """Запускает брут домена по словарю и поиск субдоменов по crt_sh

        Returns:
            list[str]: Список доменов
        """
        tasks = []
        tasks = [asyncio.create_task(self.Domain_brute.query(self.domain, dict_file=self.dict_file, query_type = "A"))]
        if self.crt_sh:
            tasks.append(asyncio.create_task(self.CrtSh.crt_sh(self.domain)))
        result = await asyncio.gather(*tasks)
        return result

    @BaseJob.remote_task_notifier
    async def run(self):
        result = await self._task_func()
        data = {
            "target_domain": self.domain,
            "raw_result": result
            }
        return data, 'json'
