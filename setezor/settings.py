import os
import platform

PATH_PREFIX = os.path.join(os.path.expanduser('~'), '.local/share/setezor')
system = platform.system()
if system == "Windows":
    PATH_PREFIX = os.path.dirname(os.path.dirname(__file__))
os.makedirs(PATH_PREFIX, exist_ok=True)
LOG_LEVEL = "INFO"
VERSION = "1.0.3"
