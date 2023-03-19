"""
Implementation of connection by the Python DBAPI 2.0 as described in
https://www.python.org/dev/peps/pep-0249/ .

"""
import logging
from upsolver.client.query import RestQueryApi
from upsolver.client.requester import Requester
from upsolver.client.auth_filler import TokenAuthFiller
from upsolver.client.exceptions import OperationalError, InterfaceError, NotSupportedError
from upsolver.dbapi.utils import get_duration_in_seconds, check_closed, DBAPIResponsePoller
from upsolver.dbapi.cursor import Cursor

logger = logging.getLogger(__name__)


def connect(token, api_url):
    logger.debug(f"Creating connection")
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
        except InterfaceError as err:
            raise InterfaceError("Timeout can't be parsed") from err
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        self.close()
        return error is None

    @check_closed
    def cursor(self):
        logger.debug(f"{self.__class__.__name__} create cursor")
        return Cursor(self)

    @check_closed
    def close(self) -> None:
        logger.debug(f"{self.__class__.__name__} close")
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
        logger.info(f'{self.__class__.__name__} execute query "{command}"')
        return self._api.execute(command, self._timeout)
