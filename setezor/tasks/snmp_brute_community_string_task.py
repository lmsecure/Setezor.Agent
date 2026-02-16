import os
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path



class SnmpBruteCommunityStringTask(BaseJob):

    module_name = "snmp"
    SnmpGettingAccess = load_class_from_path(module_name, "snmp.py", "SnmpGettingAccess")
    SnmpParser = load_class_from_path(module_name, "parser.py", "SnmpParser")


    @classmethod
    def load_module(cls):
        cls.SnmpGettingAccess = load_class_from_path(cls.module_name, "snmp.py", "SnmpGettingAccess")
        cls.SnmpParser = load_class_from_path(cls.module_name, "parser.py", "SnmpParser")
        return (cls.SnmpGettingAccess is not None) and (cls.SnmpParser is not None)

    def __init__(self, scheduler, name: str, task_id: int, project_id: str, agent_id: str,
            target_ip: str, target_port: int, community_strings_file: str):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.target_ip = target_ip
        self.target_port = target_port
        self.community_strings = self.SnmpParser.parse_community_strings_file(file = community_strings_file)
        self._coro = self.run()

    async def _task_funk(self):
        return await self.SnmpGettingAccess.brute_community_strings(ip_address=self.target_ip, port=self.target_port, community_strings=self.community_strings)

    @BaseJob.remote_task_notifier
    async def run(self):
        data = await self._task_funk()
        result = {
            "raw_result": data,
            "target_ip": self.target_ip,
            "target_port": self.target_port
        }
        return result, ""
