from setezor.tasks.base_job import BaseJob
from .dns_task import DNSTask
from .cert_task import CertTask
from .domain_task import SdFindTask
from .whois_task import WhoisTask
from .nmap_scan_task import NmapScanTask
from .scapy_scan_task import ScapySniffTask
from .masscan_scan_task import MasscanScanTask
from .snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from .dns_a_screenshot_task import DNS_A_ScreenshotTask
from .ip_info_task import IpInfoTask
from .self_hosted_agent_interfaces_task import SelfHostedAgentInterfaces
from setezor.settings import PLATFORM
if PLATFORM != "Windows":
    from .speed_test_task import SpeedTestClientTask, SpeedTestServerTask
    from .firewall_checker_task import FirewallCheckerSenderTask, FirewallCheckerSnifferTask


def get_task_by_class_name(name: str):
    model_class = globals().get(name)

    if model_class and issubclass(model_class, BaseJob):
        return model_class
    else:
        raise ValueError(
            f"Модель с именем {name} не найдена или не является SQLModel.")


def get_available_tasks():
    return {
        model.__name__: {} for model in globals().values()
        if isinstance(model, type) and issubclass(model, BaseJob) and model is not BaseJob
    }
