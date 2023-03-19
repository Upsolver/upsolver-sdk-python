import logging
from logging import Logger
from typing import Any, Dict, Optional, Protocol, Type, TypeVar
import upsolver.client.exceptions as exceptions

seconds_per_unit = {'s': 1.0, 'm': 60.0}


def convert_to_seconds(s: str) -> float:
    return float(s[:-1]) * seconds_per_unit[s[-1]]


def convert_time_str(value: Any) -> Any:
    try:
        return convert_to_seconds(value)
    except Exception:
        raise exceptions.InterfaceError(f'Cannot convert \'{value}\' to seconds '
                                      '(valid examples: 0.25s, 1.5m)')


def get_logger(path: Optional[str] = None) -> Logger:
    """
    Use this method to get logger instances. It uses the "CLI" logger as the "root" logger, thus
    all logger instances returned from this function will share the root logger's configuration.

    :param path: a dot-separated path, e.g. "Requester", or "Something.Other"
    :return:
    """
    if path is not None:
        return logging.getLogger(f'CLI.{path}')
    else:
        return logging.getLogger('CLI')

def flatten(d: dict, parent: Optional[str] = None, sep: str = '.') -> dict:
    """
    flatten({'a': {'b': {'c': 1}}, 'd': {'e': [1, 2, 3]}, 'f': 'foo'})
    returns
    {'a.b.c': 1, 'd.e': [1, 2, 3], 'f': 'foo'}

    :param d: dictionary to flatten
    :param parent: name of parent key; used for recursion
    :param sep: separator between concatenated key names
    :return: flattened dictionary
    """
    items: list = []
    for k, v in d.items():
        new_key = f'{parent}{sep}{k}' if parent is not None else k
        if type(v) is dict:
            items.extend(flatten(v, parent=new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class NestedDictAccessor(object):
    def __init__(self, d: dict) -> None:
        self.d = d

    def __getitem__(self, item: Any) -> Any:
        def throw() -> None:
            raise KeyError(f'Missing {item} in {self.d}')

        curr: Any = self.d  # type annotation is a hack...
        for path_part in item.split('.'):
            if type(curr) is not dict:
                throw()
            v = curr.get(path_part)
            if v is None:
                throw()
            curr = v
        return curr


# Protocol == structural typing support (https://peps.python.org/pep-0544/)
class AnyDataclass(Protocol):
    __dataclass_fields__: Dict


TAnyDataclass = TypeVar('TAnyDataclass', bound=AnyDataclass)


def from_dict(tpe: Type[TAnyDataclass], d: dict) -> TAnyDataclass:
    return tpe.from_dict(d)
