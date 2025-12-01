import asyncio
from typing import List
from aiojobs import Job, Scheduler
from setezor.tasks.base_job import BaseJob
from setezor.tasks.nmap_scan_task import NmapScanTask
from setezor.tasks.masscan_scan_task import MasscanScanTask
from setezor.tasks.scapy_scan_task import ScapySniffTask
from setezor.tasks.ip_info_task import IpInfoTask
from setezor.tasks.snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from setezor.interfaces.observer import Observable, Observer


class CustomScheduler(Scheduler, Observable, Observer):
    def __init__(self, *args, **kwrags):
        super().__init__(*args, **kwrags)
        self._observers = []

    def attach(self, observer: Observer) -> None:
        self._observers.append(observer)

    def detach(self, observer: Observer) -> None:
        self._observers.remove(observer)

    async def notify(self,
                     agent_id: str,
                     data: dict) -> None:
        for observer in self._observers:
            await observer.notify(agent_id=agent_id,
                                  data=data)
    
    async def give_result_to_task_manager(self,
                                          task_id: str,
                                          agent_id: str,
                                          result: dict,
                                          raw_result_extension: str):
        for observer in self._observers:
            await observer.send_result_to_parent_agent(agent_id=agent_id,
                                                       task_id=task_id,
                                                       task_data=result,
                                                       raw_result_extension=raw_result_extension)

    async def spawn_job(self, job: BaseJob) -> Job:
        if self._closed:
            raise RuntimeError("Scheduling a new job after closing")
        should_start = self._limit is None or self.active_count < self._limit
        if should_start:
            job._start()
        else:
            try:
                await self._pending.put(job)
            except asyncio.CancelledError:
                await job.close()
                raise
        self._jobs.add(job)
        return job

    @property
    def jobs(self):
        return self._jobs


class SchedulerManager:
    settings = {
        NmapScanTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        MasscanScanTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        ScapySniffTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        SnmpBruteCommunityStringTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        },
        IpInfoTask: {
            "close_timeout": 0.1,
            "wait_timeout": 60,
            "limit": 1,
            "pending_limit": 10000
        }
    }

    @classmethod
    def for_job(cls, job: BaseJob):
        if job in cls.settings:
            return CustomScheduler(**cls.settings[job])
        return CustomScheduler()
