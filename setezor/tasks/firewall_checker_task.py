from .base_job import BaseJob
from setezor.modules.firewall_checker.sender import Sender
from setezor.modules.firewall_checker.sniffer import Sniffer



class FirewallCheckerSenderTask(BaseJob):

    def __init__(self, scheduler, name: str, project_id: str, task_id: int, agent_id: int,
                 sniffer_task_id: str,
                 interface_name: str,
                 ip_id_from: str,
                 ip_id_to: str,
                 target_ip: str,
                 protocol: int = 0,
                 payload_salt: int = 0,
                 rate: int = 100,
                 target_ports: str = "",
                 source_port: int = 0,
                 count_retries: int = 2,
                 verbose: bool = False, **kwargs):
        super().__init__(scheduler = scheduler, name = name)
        self.sniffer_task_id = sniffer_task_id
        self.interface_name = interface_name
        self.target_ip = target_ip
        self.protocol = protocol
        self.payload_salt = payload_salt
        self.rate = rate
        self.target_ports = target_ports
        self.source_port = source_port
        self.packet_count = count_retries + 1
        self.verbose = verbose

        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self._coro = self.run()


    async def _task_func(self):
        await Sender.start(
            sender_id=self.task_id,
            interface_name=self.interface_name,
            target_ip=self.target_ip,
            protocol=self.protocol,
            payload_salt=self.payload_salt,
            rate=self.rate,
            target_ports=self.target_ports,
            source_port=self.source_port,
            packet_count=self.packet_count,
            verbose=self.verbose)


    async def soft_stop(self):
        await Sender.finish(sender_id=self.task_id)


    @BaseJob.remote_task_notifier
    async def run(self):
        await self._task_func()
        return {}, ''



class FirewallCheckerSnifferTask(BaseJob):

    def __init__(self, scheduler, name: str, project_id: str, task_id: int, agent_id: int,
                 ip_id_from: str,
                 ip_id_to: str,
                 protocol: int = 0,
                 payload_salt:int = 0,
                 verbose: bool = False, **kwargs):
        super().__init__(scheduler = scheduler, name = name)
        self.protocol = protocol
        self.payload_salt = payload_salt
        self.verbose = verbose

        self.ip_id_from = ip_id_from
        self.ip_id_to = ip_id_to
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.agent_id_from = kwargs.get("agent_id_from")
        self._coro = self.run()


    async def _task_func(self) -> str:
        return await Sniffer.start(
            sniffer_id=self.task_id,
            protocol=self.protocol,
            payload_salt=self.payload_salt,
            verbose=self.verbose)


    async def soft_stop(self):
        await Sniffer.finish(sniffer_id=self.task_id)

    @BaseJob.remote_task_notifier
    async def run(self):
        discovered_ports = await self._task_func()
        result = {
            "ip_id_from" : self.ip_id_from,
            "ip_id_to" : self.ip_id_to,
            "discovered_ports" : discovered_ports,
            "protocol" : ["TCP", "UDP"][self.protocol]
        }
        return result, ''