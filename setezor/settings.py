import os
import platform


PLATFORM = platform.system()
PYTHON_VERSION = platform.python_version()
VERSION = "1.0.5"
LOG_LEVEL = "INFO"

suffix = [".local", "share", "setezor"]
if PLATFORM == "Windows":
    suffix = ["AppData", "Local", "setezor"]
PATH_PREFIX = os.path.join(os.path.expanduser('~'), *suffix)
os.makedirs(PATH_PREFIX, exist_ok=True)
