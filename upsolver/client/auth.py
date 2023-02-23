from abc import ABCMeta, abstractmethod

from upsolver.client.errors import InternalErr


class AuthApi(metaclass=ABCMeta):
    @abstractmethod
    def authenticate(self, email: str, password: str):
        pass
