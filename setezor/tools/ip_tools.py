import socket
import ipaddress
import psutil
import platform
from setezor.network_structures import InterfaceStruct
from setezor.settings import PLATFORM

if PLATFORM == "Windows":
    import wmi


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
    """Returns interface list"""

    interfaces = []
    for name, addrs in psutil.net_if_addrs().items():
        for addr in addrs:
            if addr.family == socket.AF_INET:
                interfaces.append(InterfaceStruct(name=name, ip=addr.address, mac=addr.netmask))
    return interfaces


def get_interface(interface: str) -> str | None:
    if PLATFORM == "Windows":
        for network_adapter in wmi.WMI().Win32_NetworkAdapter(NetEnabled=True):
            if network_adapter.NetConnectionID == interface:
                return f"\\Device\\NPF_{network_adapter.GUID}"
        return None
    else:
        return interface


def is_ip_address(address):
        try:
            socket.inet_aton(address)
            return True
        except OSError:
            return False


def get_network(ip: str, mask: int) -> tuple[str:, str]:
    """ Функция получения инвормации о подсети по ip и маске

    Returns:
        tuple: (start_ip, broadcast)
    """

    network = ipaddress.ip_network(f"{ip}/{mask}", strict=False)
    start_ip = str(network.network_address)
    broadcast = str(network.broadcast_address)
    return start_ip, broadcast