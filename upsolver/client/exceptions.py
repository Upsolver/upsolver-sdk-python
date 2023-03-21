import json
from json import JSONDecodeError
from typing import Optional
from upsolver.client.response import UpsolverResponse


class Error(Exception):
    """Base error outlined in PEP 249."""


class InterfaceError(Error):
    """
    Interface error outlined in PEP 249.

    Raised for errors with the database interface.

    """


class DatabaseError(Error):
    """
    Database error outlined in PEP 249.

    Raised for errors with the database.

    """
class OperationalError(DatabaseError):
    """
    Operational error outlined in PEP 249.

    Raised for errors in the database's operation.

    """


class NotSupportedError(DatabaseError, NotImplementedError):
    """
    Not supported error outlined in PEP 249.

    Raised when an unsupported operation is attempted.

    """


class ApiError(OperationalError):
    """
    Invalid usage of API (invalid credentials, bad method call).
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
