import os
import platform

PATH_PREFIX = os.path.join(os.path.expanduser('~'), '.local/share/setezor')
system = platform.system()
if system == "Windows":
    PATH_PREFIX = os.path.dirname(os.path.dirname(__file__))
LOG_LEVEL = "INFO"