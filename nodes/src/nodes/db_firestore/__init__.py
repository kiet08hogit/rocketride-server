import os
from depends import depends  # type: ignore

requirements = os.path.dirname(os.path.realpath(__file__)) + '/requirements.txt'
depends(requirements)

from .IGlobal import IGlobal  # noqa: E402
from .IInstance import IInstance  # noqa: E402

__all__ = ['IGlobal', 'IInstance']
