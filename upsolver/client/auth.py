from abc import ABCMeta, abstractmethod

class AuthApi(metaclass=ABCMeta):
    @abstractmethod
    def authenticate(self, email: str, password: str):
        pass
