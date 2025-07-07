import socket
import ipaddress
import subprocess
import psutil
import re
from setezor.network_structures import InterfaceStruct


def get_nmap_interfaces() -> dict[str, str]:
    """Parses `nmap --iflist` and returns {ip: nmap_name}"""
    output = subprocess.check_output(["nmap", "--iflist"], text=True)
    ip_to_nmap = {}

    for line in output.splitlines():
        match = re.search(r"^\s*(\S+)\s+\(\S+\)\s+(\d+\.\d+\.\d+\.\d+)/\d+", line)
        if match:
            nmap_name, ip = match.groups()
            ip_to_nmap[ip.strip()] = nmap_name.strip()

    return ip_to_nmap


def get_ipv4(interface: str) -> str | None:
    for addr in psutil.net_if_addrs().get(interface, []):
        if addr.family == socket.AF_INET:
            return addr.address
    return None


def get_mac(interface: str) -> str | None:
    for addr in psutil.net_if_addrs().get(interface, []):
        if addr.family == psutil.AF_LINK:
            return addr.address.upper().replace("-", ":")
    return None


def get_interfaces() -> list[InterfaceStruct]:
    """Returns interface list using `nmap`-style names like eth0, lo0"""
    interfaces = []
    ip_to_nmap = get_nmap_interfaces()

    for iface_name, addrs in psutil.net_if_addrs().items():
        ipv4 = get_ipv4(iface_name)
        mac = get_mac(iface_name)

        if ipv4 and ipv4 in ip_to_nmap:
            interfaces.append(InterfaceStruct(
                name=iface_name,
                ip=ipv4,
                mac=mac
            ))

    return interfaces
