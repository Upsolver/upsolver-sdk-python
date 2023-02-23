import requests

def generate_local_api_token(user_email: str, user_password: str, url: str) -> str:
    data = {
        "displayData": {
            "name": "local",
            "description": ""
        }
    }
    headers = {
        "X-Api-Email": user_email,
        "X-Api-Password": user_password
    }
    response = requests.post(f"{url}/api-tokens", json=data, headers=headers)
    api_token = response.json()["apiToken"]
    return api_token
