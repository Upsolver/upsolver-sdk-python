"""
Implementation of cursor by the Python DBAPI 2.0 as described in
https://www.python.org/dev/peps/pep-0249/ .

"""
import logging
from pathlib import Path
from typing import Optional, Sequence, Type, Union

from ..client import errors as upsolver_errors

from .utils import check_closed
from .exceptions import *
from .types_definitions import (
    QueryParameters,
    ResultRow,
    ResultSet,
    SQLQuery,
    ColumnDescription,
    ProcName,
    ProcArgs,
)

logger = logging.getLogger(__name__)


class Cursor:
    """A PEP 249 compliant Cursor protocol."""
    def __init__(self, connection):
        self._connection = connection
        self._arraysize = 1
        self._rowcount = -1
        self._description = None
        self._iterator = None
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, error_type, error, traceback):
        self.close()
        return error is None

    @check_closed
    def execute(self, operation: SQLQuery, parameters: Optional[QueryParameters] = None):
        """
        Execute an SQL query. Values may be bound by passing parameters
        as outlined in PEP 249.

        """
        logger.debug(f'{self.__class__.__name__} execute query "{operation}"')
        if parameters is not None:
            raise NotSupportedError

        try:
            query_response = self._connection.query(operation)
            return self._prepare_query_results(query_response)
        except upsolver_errors.InternalErr as err:
            raise InternalError(err) from err
        except upsolver_errors.RequestErr as err:
            raise OperationalError(err) from err
        except Exception as err:
            raise DatabaseError(err) from err

    @check_closed
    def executefile(self, file_path: str):
        """
        Execute an SQL query from file.
        """
        logger.debug(f'{self.__class__.__name__} executefile with file "{file_path}"')

        p = Path(file_path)
        if not p.exists():
            raise InterfaceError(f'Failed to execute the operation because {file_path} is invalid')
        operation = p.read_text()
        return self.execute(operation)

    def _prepare_query_results(self, query_response):
        first_response = next(query_response)
        if 'data' in first_response:
            self._rowcount = -1 if first_response.get('has_next_page', True) else len(first_response['data'])
            self._description = [(c['name'], c['columnType'].get('clazz'), None, None, None, None, None)
                                 for c in first_response['columns']]
        else:
            self._rowcount = -1
            self._description = None
        self._iterator = self._generate_rows(first_response, query_response)
        return self._iterator

    @staticmethod
    def _generate_rows(first_page, next_pages):
        if 'data' in first_page:
            for row in first_page['data']:
                yield row
        elif first_page.get('message'):
            yield first_page.get('message')

        for next_page in next_pages:
            if 'data' in next_page:
                for row in next_page['data']:
                    yield row
            elif next_page.get('message'):
                yield next_page.get('message')

    def executemany(self, operation: SQLQuery, seq_of_parameters: Sequence[QueryParameters]):
        raise NotSupportedError

    def callproc(self, procname: ProcName, parameters: Optional[ProcArgs] = None) -> Optional[ProcArgs]:
        raise NotSupportedError

    @property
    @check_closed
    def description(self) -> Optional[Sequence[ColumnDescription]]:
        """
        A read-only attribute returning a sequence containing a description
        (a seven-item sequence) for each column in the result set. The first
        item of the sequence is a column name, the second is a column type,
        which is always STRING in current implementation, other items are not
        meaningful.

        If no execute has been performed or there is no result set, return None.
        """
        logger.debug(f"{self.__class__.__name__} get description")
        return self._description

    @property
    @check_closed
    def rowcount(self) -> int:
        """
        If no execute has been performed or the rowcount cannot be determined,
        this should return -1.
        """
        logger.debug(f"{self.__class__.__name__} get rowcount")
        return self._rowcount

    @property
    @check_closed
    def arraysize(self) -> int:
        """
        An attribute specifying the number of rows to fetch at a time with
        `fetchmany`.

        Defaults to 1, meaning fetch a single row at a time.
        """
        logger.debug(f"{self.__class__.__name__} get arraysize")

        return self._arraysize

    @arraysize.setter
    @check_closed
    def arraysize(self, value: int):
        logger.debug(f"{self.__class__.__name__} set arraysize")

        if value > 0:
            self._arraysize = value
        else:
            raise ValueError('arraysize should be a positive number')

    @check_closed
    def fetchone(self) -> Optional[ResultRow]:
        """
        Fetch the next row from the query result set as a sequence of Python
        types (or return None when no more rows are available).

        If the previous call to `execute` did not produce a result set, an
        error can be raised.

        """
        logger.debug(f"Fetchone {self.__class__.__name__}")

        if self._iterator is None:
            raise InterfaceError('Failed to fetch results')

        try:
            return next(self._iterator)
        except StopIteration:
            return None

    @check_closed
    def fetchmany(self, size: Optional[int] = None) -> Optional[ResultSet]:
        """
        Fetch the next `size` rows from the query result set as a list
        of sequences of Python types.

        If the size parameter is not supplied, the arraysize property will
        be used instead.

        If rows in the result set have been exhausted, an an empty list
        will be returned. If the previous call to `execute` did not
        produce a result set, an error can be raised.

        """
        logger.debug(f"{self.__class__.__name__} fetchmany")

        if self._iterator is None:
            raise InterfaceError('Failed to fetch results')

        result = []
        for _ in range(size or self.arraysize):
            row = self.fetchone()
            if row is None:
                break
            result.append(row)

        return result

    @check_closed
    def fetchall(self) -> ResultSet:
        """
        Fetch the remaining rows from the query result set as a list of
        sequences of Python types.

        If rows in the result set have been exhausted, an an empty list
        will be returned. If the previous call to `execute` did not
        produce a result set, an error can be raised.

        """
        logger.debug(f"{self.__class__.__name__} fetchall")

        if self._iterator is None:
            raise InterfaceError('Failed to fetch results')

        result = []
        while True:
            row = self.fetchone()
            if row is None:
                break
            result.append(row)

        return result

    @check_closed
    def nextset(self) -> Optional[bool]:
        raise NotSupportedError

    def setinputsizes(self, sizes: Sequence[Optional[Union[int, Type]]]) -> None:
        raise NotSupportedError

    def setoutputsize(self, size: int, column: Optional[int]) -> None:
        raise NotSupportedError

    @check_closed
    def close(self) -> None:
        logger.debug(f"{self.__class__.__name__} close")
        self._closed = True

    @property
    def closed(self) -> bool:
        return self._closed
