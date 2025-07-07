import signal
import psutil
import os
from setezor.tasks.base_job import BaseJob
from setezor.modules.nmap.scanner import NmapScanner
import platform

system = platform.system()
if system == "Linux":
    from setezor.tools.ip_tools import get_ipv4, get_mac
else:
    from setezor.tools.ip_tools_windows import get_nmap_interfaces, get_ipv4, get_mac



class NmapScanTask(BaseJob):
    def __init__ (self, scheduler, name: str, task_id: int, project_id: str,
                        targetIP: str,
                        agent_id: int,
                        interface_ip_id: int,
                        interface: str,
                        targetPorts: str,
                        traceroute: bool,
                        serviceVersion: bool,
                        stealthScan: bool,
                        skipDiscovery: bool,
                        scanTechniques: str = '',
                        portsDiscovery: str = '',
                        requestDiscovery: str = ''):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.interface_ip_id = interface_ip_id
        self.interface = interface
        self.ip = get_ipv4(self.interface)
        self.mac = get_mac(self.interface)
        if system == "Windows":
            self.interface = get_nmap_interfaces()[self.ip]
        self.extra_args = [targetIP, targetPorts]
        if traceroute: self.extra_args.append("--traceroute")
        if serviceVersion: self.extra_args.append("-sV")
        if stealthScan: self.extra_args.append("-O")
        if skipDiscovery: self.extra_args.append("-Pn")
        if scanTechniques: self.extra_args.append(scanTechniques)
        if portsDiscovery: self.extra_args.append(portsDiscovery)
        if requestDiscovery: self.extra_args.append(requestDiscovery)
        self.extra_args.append("-e " + self.interface)
        self.extra_args.append("-n")
        # self.extra_args.append("-d4")
        self.pid = None
        self._coro = self.run()


    async def _task_func(self):
        raw_result = await NmapScanner(self).async_run(extra_args=' '.join(self.extra_args), _password=None)
        data = {
            "raw_result": raw_result,
            "agent_id": self.agent_id,
            "self_address": {
                'ip': self.ip, 
                'mac': self.mac
            },
            "interface_ip_id": self.interface_ip_id
        }
        return data
    
    async def soft_stop(self):
        for process in psutil.process_iter():
            if process.ppid() == self.pid:
                os.kill(process.pid, signal.SIGKILL)
        os.kill(self.pid, signal.SIGKILL)

    @BaseJob.remote_task_notifier
    async def run(self):
        data = await self._task_func()
        return data, "xml"