import os
from setezor.tasks.base_job import BaseJob
from setezor.tools.importer import load_class_from_path


class SpeedTestClientTask(BaseJob):

    module_name = "speed_test"
    Client = load_class_from_path(module_name, "speed_test.py", "Client")

    @classmethod
    def load_module(cls):
        cls.Client = load_class_from_path(cls.module_name, "speed_test.py", "Client")
        return cls.Client is not None


    def __init__(self, scheduler, name: str, task_id: str, agent_id: str, project_id: str,
                 ip_id_from: str, ip_id_to: str, target_port: int, target_ip: str, duration: int = 5, packet_size: int = 1400, protocol: int = 0, **kwargs):
        super().__init__(scheduler = scheduler, name = name)
        self.task_id = task_id
        self.agent_id = agent_id
        self.project_id = project_id

        self.target_ip = target_ip
        self.target_port = target_port
        self.duration = duration
        self.packet_size = packet_size
        self.protocol = protocol

        self._coro = self.run()

    async def _task_func(self) -> None:
        await self.Client.start(client_id=self.task_id,
                     target_ip=self.target_ip,
                     target_port=self.target_port,
                     duration=self.duration,
                     packet_size=self.packet_size,
                     protocol=self.protocol,
                     verbose=False)

    async def soft_stop(self):
        await self.Client.finish(client_id=self.task_id)

    @BaseJob.remote_task_notifier
    async def run(self):
        await self._task_func()
        return {}, ""



class SpeedTestServerTask(BaseJob):

    module_name = "speed_test"
    Server = load_class_from_path(module_name, "speed_test.py", "Server")

    @classmethod
    def load_module(cls):
        cls.Server = load_class_from_path(cls.module_name, "speed_test.py", "Server")
        return cls.Server is not None


    def __init__(self, scheduler, name: str, task_id: str, agent_id: str, project_id: str,
                 ip_id_from: str, ip_id_to: str, target_port: int, protocol: int = 0, **kwargs):
        super().__init__(scheduler = scheduler, name = name)
        self.task_id = task_id
        self.agent_id = agent_id
        self.project_id = project_id

        self.ip_id_from = ip_id_from
        self.ip_id_to = ip_id_to
        self.agent_id_from = kwargs.get("agent_id_from")
        self.target_port = target_port
        self.protocol = protocol

        self._coro = self.run()


    async def _task_func(self) -> float:
        return await self.Server.start(server_id=self.task_id,
                            target_port=self.target_port,
                            protocol=self.protocol,
                            verbose=False)

    async def soft_stop(self):
        await self.Server.finish(server_id=self.task_id)

    @BaseJob.remote_task_notifier
    async def run(self):
        mbps = await self._task_func()
        result = {
            "ip_id_from" : self.ip_id_from,
            "ip_id_to" : self.ip_id_to,
            "speed" : mbps,
            "port" : self.target_port,
            "protocol" : ["TCP", "UDP"][self.protocol]
        }
        return result, ""

