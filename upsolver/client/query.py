from typing import Iterator
from upsolver.client.poller import ResponsePollerBuilder
from upsolver.client.requester import Requester
from upsolver.client.exceptions import NotSupportedError

ExecutionResult = list

class RestQueryApi():
    def __init__(self, requester: Requester, poller_builder: ResponsePollerBuilder):
        self.requester = requester
        self.poller_builder = poller_builder

    def check_syntax(self, expression: str) -> list:
        raise NotSupportedError()

    def execute(self, query: str, timeout_sec: float) -> Iterator[ExecutionResult]:
        assert len(query) > 0
        poller = self.poller_builder(timeout_sec)

        (data, next_path) = poller(
            self.requester,
            self.requester.post('query', json={'sql': query})
        )
        yield data

        while next_path is not None:
            (data, next_path) = poller(self.requester, self.requester.get(next_path))
            yield data
