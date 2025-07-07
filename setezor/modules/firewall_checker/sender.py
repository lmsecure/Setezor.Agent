import os
import ctypes
import asyncio


class Sender:

    lib_path = os.path.join(os.path.dirname(__file__), "sender_lib.module")
    lib = ctypes.CDLL(lib_path)

    lib.async_sender.argtypes = [
        ctypes.c_char_p,    # sender_id (task_id)
        ctypes.c_char_p,    # interface name
        ctypes.c_char_p,    # target IP
        ctypes.c_int,       # protocol (0 for TCP, 1 for UDP)
        ctypes.c_int,       # payload salt
        ctypes.c_size_t,    # rate
        ctypes.c_char_p,    # target_ports
        ctypes.c_int,       # source port
        ctypes.c_int,       # packet count
        ctypes.c_bool       # verbose
    ]
    lib.async_sender.restype = ctypes.c_bool

    lib.is_task_work.argtypes = [ctypes.c_char_p] # sender_id (task_id)
    lib.is_task_work.restype = ctypes.c_bool

    lib.finish_task.argtypes = [ctypes.c_char_p] # sender_id (task_id)
    lib.finish_task.restype = None

    lib.getErrorInfo.restype = ctypes.c_char_p

    @classmethod
    async def start(cls,
             sender_id: str,
             interface_name: str,
             target_ip: str,
             protocol: int = 0,
             payload_salt: int = 0,
             rate: int = 100,
             target_ports: str = "",
             source_port: int = 0,
             packet_count: int = 1,
             verbose: bool = False) -> None:
        """
        Args:
            interface_name (str): The name of the network interface to use.
            target_ip (str): The target IP address for the sender.
            protocol (int, optional): The protocol to use 0 - TCP, 1 - UDP. Defaults to 0 (TCP).
            payload_salt (int, optional): The payload salt. Defaults to 0.
            rate (int, optional): The rate of packets per second. Defaults to 100.
            source_port (int, optional): The source port [1 .. 65535]. Defaults to 0 - random.
            target_ports (str): Target ports, example: "1,3,5-10...".
            packet_count (int, optional): The number of packets to send. Defaults to 3.
            verbose (bool, optional): Whether to enable verbose output. Defaults to False.
        """

        is_start = cls.lib.async_sender(
            sender_id.encode("utf-8"),
            interface_name.encode("utf-8"),
            target_ip.encode("utf-8"),
            protocol,
            payload_salt,
            rate,
            target_ports.encode("utf-8"),
            source_port,
            packet_count,
            verbose
        )
        if not is_start:
            raise Exception(cls.lib.getErrorInfo().decode("utf-8"))

        while cls.lib.is_task_work(sender_id.encode("utf-8")):
            await asyncio.sleep(2)

        cls.lib.finish_task(sender_id.encode("utf-8"))

    @classmethod
    async def finish(cls, sender_id: str):
        cls.lib.finish_task(sender_id.encode("utf-8"))
