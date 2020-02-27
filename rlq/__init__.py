import os.path as _path
__VERSION__ = open(_path.join(_path.dirname(__file__), 'VERSION'), 'r').read().strip()

from .utils import get_query_executor
