import time
from functools import wraps
from upsolver.client.requester import Requester
from upsolver.client.response import UpsolverResponse
from upsolver.client.poller import SimpleResponsePoller
from upsolver.utils import convert_time_str
from upsolver.client.exceptions import InterfaceError, ApiError, PayloadError, PendingResultTimeout


def get_duration_in_seconds(duration):
    if type(duration) == float:
        return duration
    if type(duration) == int:
        return float(duration)
    if type(duration) == str:
        return convert_time_str(duration)
    raise ValueError('Invalid type of duration')


def check_closed(func):
    @wraps(func)
    def wrapped(self, *args, **kwargs):
        if self.closed:
            raise InterfaceError("Object is closed and can't be used")
        return func(self, *args, **kwargs)
    return wrapped


class DBAPIResponsePoller(SimpleResponsePoller):
    def _get_result_helper(self,
                           requester: Requester,
                           resp: UpsolverResponse,
                           start_time: float = 0) -> \
            tuple:
        """
        :param start_time: time (in seconds since the Epoch) at which polling has started.
        """
        def raise_err() -> None:
            raise ApiError(resp)

        sc = resp.status_code
        if int(sc / 100) != 2:
            raise_err()

        def verify_json(j: dict) -> dict:
            if 'status' not in j:
                raise PayloadError(resp, 'expected "status" field in response object')
            return j

        def extract_json() -> dict:
            resp_json = resp.json()
            if type(resp_json) is dict:
                return resp_json
            elif type(resp_json[0]) is dict:
                if len(resp_json) > 1:
                    raise PayloadError(resp, 'got list with multiple objects')
                return resp_json[0]
            else:
                raise PayloadError(resp, 'failed to find result object')

        rjson = verify_json(extract_json())
        status = rjson['status']
        is_success = sc == 200 and status == 'Success'

        # 201 is CREATED; returned on initial creation of "pending" response
        # 202 is ACCEPTED; returned if existing pending query is still not ready
        is_pending = (sc == 201 or sc == 202) and status == 'Pending'

        if not (is_success or is_pending):
            raise_err()

        if is_pending:
            time_spent_sec = int(time.time() - start_time)
            if (self.max_time_sec is not None) and (time_spent_sec >= self.max_time_sec):
                raise PendingResultTimeout(resp)

            time.sleep(self.wait_interval_sec)
            return self._get_result_helper(
                requester=requester,
                resp=requester.get(path=rjson['current']),
                start_time=start_time,
            )

        if 'result' in rjson:
            result = rjson['result']
            result['grid']['has_next_page'] = result.get('next') is not None
            return result['grid'], result.get('next')
        else:
            return rjson, None
