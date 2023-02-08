"""
Implementation of connection by the Python DBAPI 2.0 as described in
https://www.python.org/dev/peps/pep-0249/ .

"""

from ..client.query import RestQueryApi
from ..client.requester import Requester
from ..client.auth_filler import TokenAuthFiller
from ..client import errors as upsolver_errors

from .utils import logger, get_duration_in_seconds, check_closed, DBAPIResponsePoller
from .exceptions import *
from .cursor import Cursor


def connect(token, api_url):
    logger.debug(f"pep249 Creating connection for object ")
    return Connection(token, api_url)


class Connection:
    """A PEP 249 compliant Connection protocol."""

    def __init__(self, token, api_url, timeout_sec='60s'):
        try:
            self._api = RestQueryApi(
                requester=Requester(
                    base_url=api_url,
                    auth_filler=TokenAuthFiller(token)
                ),
                poller_builder=lambda to_sec: DBAPIResponsePoller(max_time_sec=to_sec)
            )
        except Exception as err:
            raise OperationalError("Failed to initialize connection with Upsolver API") from err

        try:
            self._timeout = get_duration_in_seconds(timeout_sec)
        except upsolver_errors.InvalidOptionErr as err:
            raise InterfaceError("Timeout can't be parsed") from err
        self._closed = False

    @check_closed
    def cursor(self):
        logger.debug(f"pep249 Cursor creating for object {self.__class__.__name__}")
        return Cursor(self)

    @check_closed
    def close(self) -> None:
        logger.debug(f"pep249 close {self.__class__.__name__}")
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed

    def commit(self):
        raise NotSupportedError

    def rollback(self):
        raise NotSupportedError

    @check_closed
    def query(self, command):
        logger.debug(f"pep249 Execute query")
        return self._api.execute(command, self._timeout)
