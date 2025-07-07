import os
import ctypes
import asyncio


class Sniffer:

    lib_path = os.path.join(os.path.dirname(__file__), "sniffer_lib.module")
    lib = ctypes.CDLL(lib_path)

    lib.async_sniffer.argtypes = [
        ctypes.c_char_p,    # sniffer_id (task_id)
        ctypes.c_int,       # protocol (0 for TCP, 1 for UDP)
        ctypes.c_int,       # payload salt
        ctypes.c_bool]      # verbose
    lib.async_sniffer.restype = ctypes.c_bool

    lib.is_task_work.argtypes = [ctypes.c_char_p] # sniffer_id (task_id)
    lib.is_task_work.restype = ctypes.c_bool

    lib.get_result.argtypes = [ctypes.c_char_p] # sniffer_id (task_id)
    lib.get_result.restype = ctypes.c_char_p

    lib.finish_task.argtypes = [ctypes.c_char_p] # sniffer_id (task_id)
    lib.finish_task.restype = ctypes.c_char_p

    lib.getErrorInfo.restype = ctypes.c_char_p


    @classmethod
    async def start(cls, sniffer_id: str, protocol: int = 0, payload_salt: int = 0, verbose: bool = False) -> str:
        """
        Args:
            sniffer_id (str): sniffer_id (task_id)
            protocol (int, optional): protocol (0 for TCP, 1 for UDP). Defaults to 0.
            payload_salt (int, optional): Payload salt value. Defaults to 0.
            verbose (bool, optional): Verbose output. Defaults to False.
        """
        is_start = cls.lib.async_sniffer(
            sniffer_id.encode("utf-8"),
            protocol,
            payload_salt,
            verbose
        )
        if (not is_start):
            raise Exception(cls.lib.getErrorInfo().decode("utf-8"))
        while cls.lib.is_task_work(sniffer_id.encode("utf-8")):
            await asyncio.sleep(2)
        return cls.lib.get_result(sniffer_id.encode("utf-8")).decode("utf-8")


    @classmethod
    async def finish(cls, sniffer_id: str):
        cls.lib.finish_task(sniffer_id.encode("utf-8"))