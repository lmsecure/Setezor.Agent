import struct
import sys
import os
import sysconfig
import platform



def get_abi_tag() -> str:
    soabi = sysconfig.get_config_var("SOABI")
    if soabi:
        if soabi.startswith("cpython-"):
            return f"cp{sys.version_info.major}{sys.version_info.minor}"
        if "abi3" in soabi:
            return "abi3"
    return f"cp{sys.version_info.major}{sys.version_info.minor}"


PLATFORM = platform.system()
ARCH = platform.machine().lower()
PYTHON_VERSION = f"{sys.version_info.major}{sys.version_info.minor}"
IMPLEMENTATION = sys.implementation.name[:2]
ABI = get_abi_tag()

if PLATFORM == "Windows":
    PLATFORM_TAG = f"win_{ARCH}"
elif PLATFORM == "Darwin":
    PLATFORM_TAG = "macosx_10_9_x86_64" if ARCH == "x86_64" else "macosx_11_0_arm64"
elif PLATFORM == "Linux":
    PLATFORM_TAG = f"manylinux2014_{ARCH}"  # или musllinux_1_2_{ARCH} для musl
else:
    raise RuntimeError(f"Unsupported system: {PLATFORM}")


def get_platform_name() -> str:
    if PLATFORM == 'Windows':
        if 'PROCESSOR_ARCHITEW6432' in os.environ:
            return "win64"
        return 'win64' if os.environ.get('PROCESSOR_ARCHITECTURE', '').lower() == 'amd64' else 'win32'
    bits = struct.calcsize('P') * 8
    return (PLATFORM + str(bits)).lower()

VERSION = "1.0.6.1"
LOG_LEVEL = "INFO"
current_port: int = 16662

suffix = [".local", "share", "setezor"]
if PLATFORM == "Windows":
    suffix = ["AppData", "Local", "setezor"]
PATH_PREFIX = os.path.join(os.path.expanduser('~'), *suffix)
LOG_DIR_PATH = os.path.join(PATH_PREFIX, 'agent_logs')
MODULES_PATH = os.path.join(PATH_PREFIX, 'modules')
os.makedirs(PATH_PREFIX, exist_ok=True)
os.makedirs(LOG_DIR_PATH, exist_ok=True)
os.makedirs(MODULES_PATH, exist_ok=True)
