import pandas as pd
from upsolver.client import requester, auth_filler, poller, query
from upsolver.sdk.utils import generate_local_api_token


class UpsolverApi:
    def __init__(self, token: str = None, env: str = None, user_email: str = None, user_password: str = None):
        self.token = token
        if env == 'local':
            self.base_url = 'http://localhost:8080'
            self.token = generate_local_api_token(user_email, user_password, self.base_url)
        else:
            pass

        self.api = self.__get_api(self.token, self.base_url)

    def __get_api(self, token: str, url: str = None):
        if not url:
            url = self.base_url
        token_filler = auth_filler.TokenAuthFiller(token)
        request = requester.Requester(url, token_filler)
        poll = lambda to_sec: poller.SimpleResponsePoller(max_time_sec=to_sec)
        upsolver_api = query.RestQueryApi(request, poll)
        return upsolver_api

    def execute_command(self, sql: str, timeout: int = 100):
        result = self.api.execute(sql, timeout)
        return next(result)[0]

    def query_to_df(self, sql: str, timeout: int = 100):
        data = self.api.execute(sql, timeout)
        return pd.json_normalize(next(data))


if __name__ == "__main__":
    api = UpsolverApi()
    print(api)
