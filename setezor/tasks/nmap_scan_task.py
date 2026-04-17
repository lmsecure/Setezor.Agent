import signal
import psutil
import os
import json
from setezor.tasks.base_job import BaseJob
from setezor.tools.ip_tools import get_ipv4, get_mac
from setezor.settings import PLATFORM

from setezor.tools.importer import load_class_from_path
from setezor.tools.ip_tools import get_ipv4, get_mac



class NmapScanTask(BaseJob):

    module_name = "nmap"
    description = json.dumps({
        "name": "NMAP", 
        "description": ""
    })
    NmapScanner = load_class_from_path(module_name, "scanner.py", "NmapScanner")

    @classmethod
    def load_module(cls):
        cls.NmapScanner = load_class_from_path(cls.module_name, "scanner.py", "NmapScanner")
        return cls.NmapScanner is not None


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
                        requestDiscovery: str = '',
                        timingTemplate: str | None = None,
                        minRtt: str | None = None,
                        maxRtt: str | None = None,
                        initialRtt: str | None = None,
                        maxRetries: str | None = None,
                        scanDelay: str | None = None,
                        maxTcpDelay: str | None = None,
                        maxUdpDelay: str | None = None,
                        hostTimeout: str | None = None,
                        minRate: str | None = None,
                        maxRate: str | None = None,
                        maxParallelism: str | None = None):
        super().__init__(scheduler=scheduler, name=name)
        self.task_id = task_id
        self.project_id = project_id
        self.agent_id = agent_id
        self.interface_ip_id = interface_ip_id
        self.ip = get_ipv4(interface)
        self.mac = get_mac(interface)
        self.interface = interface
        self.extra_args = ["-e"]
        if PLATFORM == "Windows":
            self.interface = self.ip
            self.extra_args = ["-S"]
        self.extra_args.extend([self.interface, targetIP] + targetPorts.split())
        if traceroute: self.extra_args.append("--traceroute")
        if serviceVersion: self.extra_args.append("-sV")
        if stealthScan: self.extra_args.append("-O")
        if skipDiscovery: self.extra_args.append("-Pn")
        if scanTechniques: self.extra_args.append(scanTechniques)
        if portsDiscovery: self.extra_args.append(portsDiscovery)
        if requestDiscovery: self.extra_args.append(requestDiscovery)
        if timingTemplate and timingTemplate in [f'T{i}' for i in range(6)]:
            self.extra_args.append(f"-{timingTemplate}")
        if minRtt:
            self.extra_args.append("--min-rtt-timeout")
            self.extra_args.append(minRtt)
        if maxRtt:
            self.extra_args.append("--max-rtt-timeout")
            self.extra_args.append(maxRtt)
        if initialRtt:
            self.extra_args.append("--initial-rtt-timeout")
            self.extra_args.append(initialRtt)
        if maxRetries:
            self.extra_args.append("--max-retries")
            self.extra_args.append(maxRetries)
        if scanDelay:
            self.extra_args.append("--scan-delay")
            self.extra_args.append(scanDelay)
        if maxTcpDelay:
            self.extra_args.append("--max-scan-delay")
            self.extra_args.append(maxTcpDelay)
        if hostTimeout and hostTimeout != "0":
            self.extra_args.append("--host-timeout")
            self.extra_args.append(hostTimeout)
        if minRate:
            self.extra_args.append("--min-rate")
            self.extra_args.append(minRate)
        if maxRate:
            self.extra_args.append("--max-rate")
            self.extra_args.append(maxRate)
        if maxParallelism:
            self.extra_args.append("--max-parallelism")
            self.extra_args.append(maxParallelism)
        self.extra_args.append("-n")
        # self.extra_args.append("-d4")
        self.pid = None
        self._coro = self.run()


    async def _task_func(self):
        raw_result = await self.NmapScanner(self).async_run(extra_args=self.extra_args, _password=None)
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