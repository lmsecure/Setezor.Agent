from setezor.tasks.base_job import BaseJob

from .dns_task import DNSTask
from .cert_task import CertTask
from .domain_task import SdFindTask
from .whois_task import WhoisTask
from .whois_shdws_task import WhoisShdwsTask
from .rdap_task import RdapTask
from .nmap_scan_task import NmapScanTask
from .scapy_scan_task import ScapySniffTask
from .masscan_scan_task import MasscanScanTask
from .snmp_brute_community_string_task import SnmpBruteCommunityStringTask
from .ip_info_task import IpInfoTask
from .self_hosted_agent_interfaces_task import SelfHostedAgentInterfaces
from .push_module_task import PushModuleTask
from .parse_site_task import ParseSiteTask

from setezor.settings import PLATFORM

# Платформозависимые импорты
if PLATFORM != "Windows":
    from .speed_test_task import SpeedTestClientTask, SpeedTestServerTask
    from .firewall_checker_task import FirewallCheckerSenderTask, FirewallCheckerSnifferTask
