
import json
from abc import ABCMeta
from json import JSONDecodeError
from typing import Optional

from yarl import URL

from upsolver.client.requester import UpsolverResponse


"""

                                                     ┌───────┐
                                                     | Error |
                                                     └───────┘
                                                         ▲
                                                         │
                                  ┌──────────────────────────────────────────────────────────┐
                          ┌───────┴───────┐                                           ┌──────┴─────────┐
                          │ DatabaseError │                                           | InterfaceError |
                          └───────────────┘                                           └────────────────┘
                                  ▲                                                          |
                                  │                                                ┌─────────┴──────────┐
       ┌──────────────────────────┬───────────────────────────┐                    | InvalidOptionError |
┌──────┴────────┐        ┌────────┴──────────┐        ┌───────┴──────────┐         └────────────────────┘
| InternalError |        | NotSupportedError |        | OperationalError |
└───────────────┘        └───────────────────┘        └──────────────────┘
                                                              ▲
                                                              |
                                       ┌──────────────────────┴────────────────────────┐
                                ┌──────┴───────┐                                ┌──────┴─────────┐
                                │ RequestError │                                | ApiUnavailable |
                                └──────────────┘                                └────────────────┘
                                       ▲
                                  ┌────┴─────┐
                                  | ApiError |
                                  └──────────┘
                                       ▲
          ┌────────────────────────────┴────────────────────────────────────────────────┐
┌─────────┴───────────┐      ┌─────────┴─────────────┐      ┌─────┴────────┐      ┌─────┴─────┐
│ PayloadPathKeyError │      │ PendingResultTimeout  │      | PayloadError |      | AuthError |
└─────────────────────┘      └───────────────────────┘      └──────────────┘      └───────────┘

"""

class Error(Exception, metaclass=ABCMeta):
    """Base error outlined in PEP 249."""

    def __str__(self) -> str:
        # make an effort to extract a message
        for msg in [m for m in self.args if type(m) == str]:
            return msg

        return self.__class__.__name__

class InterfaceError(Error):
    """
    Interface error outlined in PEP 249.

    Raised for errors with the database interface.

    """


class InvalidOptionError(InterfaceError):
    """
    Operational error outlined in PEP 249.

    Raised for errors in the database's operation.

    """

class DatabaseError(Error, RuntimeError):
    """
    Database error outlined in PEP 249.

    Raised for errors with the database.

    """
class OperationalError(DatabaseError):
    """
    Operational error outlined in PEP 249.

    Raised for errors in the database's operation.

    """

class InternalError(DatabaseError):
    """
    Integrity error outlined in PEP 249.

    Raised when the database encounters an internal error.

    """


class NotSupportedError(DatabaseError, NotImplementedError):
    """
    Not supported error outlined in PEP 249.

    Raised when an unsupported operation is attempted.

    """


class RequestError(OperationalError):
    """
    Generalized error that occured when issuing a request to the Upsolver API
    """
    pass


class ApiError(RequestError):
    """
    Invalid usage of API (invalid credentials, bad method call). In other words, we have a valid
    http response object available and the status code is not 2XX.
    """

    def __init__(self, resp: UpsolverResponse) -> None:
        self.resp = resp

    def detail_message(self) -> Optional[str]:
        """
        Make an effort to provide a clean error message about why the API call failed.
        """
        try:
            j = json.loads(self.resp.text)
            if type(j) is str:
                return j
            elif j is not None and j.get('clazz') == 'ForbiddenException':
                return j.get('detailMessage')
            elif j is not None and j.get('message') is not None:
                return j.get('message')
            else:
                # default to just returning the payload; not pretty but better than nothing
                return self.resp.text
        except JSONDecodeError:
            return self.resp.text

    def _get_error_type_name(self) -> str:
        if self.resp.status_code == 400:
            return "Syntax Error"
        else:
            return "API Error"

    def __str__(self) -> str:
        req_id_part = f'request_id={self.resp.request_id()}' \
            if self.resp.request_id() is not None \
            else ''

        error_type_name = self._get_error_type_name()

        return f'{error_type_name} : ' \
               f'{self.detail_message()} [{req_id_part}]'


class AuthError(ApiError):
    def __str__(self) -> str:
        return 'Authentication error, please run \'login\' command to create a valid token'

class PayloadError(ApiError):
    def __init__(self, resp: UpsolverResponse, msg: str):
        super().__init__(resp)
        self.msg = msg

    def __str__(self) -> str:
        return f'Payload err ({self.msg}): {self.resp}'



class PendingResultTimeout(ApiError):
    def __init__(self, resp: UpsolverResponse):
        super().__init__(resp)

    def __str__(self) -> str:
        req_id_part = f', request_id={self.resp.request_id()}' \
            if self.resp.request_id() is not None \
            else ''

        return f'Timeout while waiting for results to become ready{req_id_part}'


class PayloadPathKeyError(ApiError):
    """
    describes failure to access some path within (json) dictionary of response's payload.
    """

    def __init__(self, resp: UpsolverResponse, bad_path: str):
        """
        :param resp: response object
        :param bad_path: e.g. "x.y.z" means we attempted to access field z within y within x
        """
        super().__init__(resp)
        self.bad_path = bad_path

    def __str__(self) -> str:
        req_id_part = f' [request_id={self.resp.request_id()}]' \
            if self.resp.request_id() is not None \
            else ''

        return f'Api Error{req_id_part}: failed to find {self.bad_path} in response payload' \
               f'{self.resp.payload}'


class ApiUnavailable(OperationalError):

    def __init__(self, base_url: URL) -> None:
        self.base_url = base_url

    def __str__(self) -> str:
        return f'Failed to retrieve API address from {self.base_url}'
