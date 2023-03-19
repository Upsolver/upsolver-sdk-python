import pytest
import requests
from upsolver.client.auth_filler import AuthFiller, TokenAuthFiller

@pytest.mark.parametrize('filler', [TokenAuthFiller('token')])
def test_creates_new_req_object(filler: AuthFiller):
    print(filler)
    before = requests.Request()
    after = filler(before)
    assert before is not after
