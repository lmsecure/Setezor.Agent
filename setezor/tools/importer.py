import importlib
import sys
import os
import stat
from typing import Any, Type
from setezor.settings import PATH_PREFIX, PLATFORM


def load_class_from_path(module_name: str, file_name: str, class_name: str) -> Type[Any]:
    file_path = os.path.join(PATH_PREFIX, "modules", module_name, file_name)
    external_path = os.path.join(PATH_PREFIX, "modules", module_name, "external")
    if not os.path.isfile(file_path):
        if sys.modules.get(class_name):
            clear_sys(class_name=class_name, external_path=external_path)
        return None
    if os.path.isdir(external_path) and external_path not in sys.path:
        sys.path.insert(0, external_path)
    spec = importlib.util.spec_from_file_location(class_name, file_path)
    if spec is None:
        raise ImportError(f"Cannot load spec for {class_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[class_name] = module
    try:
        spec.loader.exec_module(module)
    except FileNotFoundError:
        return None
    try:
        return getattr(module, class_name)
    except AttributeError:
        raise ImportError(f"Class '{class_name}' not found in module '{module_name}'")


def clear_sys(class_name: str, external_path: str):
    module = sys.modules.pop(class_name)
    if external_path in sys.path:
        sys.path.remove(external_path)


def add_permissions(module_name: str, *path_args):
    if PLATFORM == 'Linux':
        file_path = os.path.join(PATH_PREFIX, "modules", module_name, *path_args)
        st = os.stat(file_path)
        os.chmod(file_path, st.st_mode | stat.S_IXUSR)
