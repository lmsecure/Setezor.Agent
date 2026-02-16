import asyncio
import os
from time import time
import base64
from setezor.settings import PATH_PREFIX
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path



class ScapySniffTask(BaseJob):

    module_name = "scapy"
    ScapySniffer = load_class_from_path(module_name, "scapy_sniffer.py", "ScapySniffer")


    @classmethod
    def load_module(cls):
        cls.ScapySniffer = load_class_from_path(cls.module_name, "scapy_sniffer.py", "ScapySniffer")
        return cls.ScapySniffer is not None

    def __init__(self, scheduler, iface: str, agent_id: int, task_id: int, name: str, project_id: str):
        super().__init__(scheduler=scheduler, name=name)
        self.agent_id = agent_id
        self.project_id = project_id
        self.iface = iface
        self.task_id = task_id
        self.is_stopped = False
        self.sniffer = self.ScapySniffer(iface=iface)
        self._coro = self.run()


    async def soft_stop(self):
        self.is_stopped = True

    def get_result(self):
        logs = self.sniffer.stop_sniffing()
        data = {"raw_result": base64.b64encode(logs).decode(), "agent_id": self.agent_id}
        return data, "pcap"

    @BaseJob.remote_task_notifier
    async def run(self):
        self.sniffer.start_sniffing()
        self.t1 = time()
        while self.sniffer.sniffer.running:
            await asyncio.sleep(2)
            if self.is_stopped:
                return self.get_result()
            if not self.sniffer.sniffer.thread.is_alive():
                raise Exception('Sniffing was failed. Maybe you dont have permission?')