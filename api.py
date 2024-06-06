import requests

def write_status(message):
    with open("status.log", "a", encoding="utf-8") as f:
        f.write(message + "\n")

class GPMLoginApiV3:
    def __init__(self, api_url, start_endpoint, close_endpoint, update_endpoint, profile_info_endpoint):
        self.api_url = api_url
        self.start_endpoint = start_endpoint
        self.close_endpoint = close_endpoint
        self.update_endpoint = update_endpoint
        self.profile_info_endpoint = profile_info_endpoint

    def start_profile(self, profile_id):
        url = f"{self.api_url}{self.start_endpoint.format(id=profile_id)}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to start profile with ID {profile_id}: {response.status_code} {response.text}")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def close_profile(self, profile_id):
        url = f"{self.api_url}{self.close_endpoint.format(id=profile_id)}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to close profile with ID {profile_id}: {response.status_code} {response.text}")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def update_proxy(self, profile_id, proxy):
        url = f"{self.api_url}{self.update_endpoint.format(id=profile_id)}"
        data = {
            "raw_proxy": proxy
        }
        try:
            response = requests.post(url, json=data)
            if response.status_code == 200:
                message = f"Run with proxy: {proxy}"
                write_status(message)
                return response.json()
            else:
                print(f"Failed to update proxy for profile with ID {profile_id}: {response.status_code} {response.text}")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def get_profile_info(self, profile_id):
        url = f"{self.api_url}{self.profile_info_endpoint.format(id=profile_id)}"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get profile info with ID {profile_id}: {response.status_code} {response.text}")
                return None
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            return None

def get_proxy_country(api, profile_id):
    profile_info = api.get_profile_info(profile_id)
    if profile_info and profile_info.get('data') and profile_info['data'].get('raw_proxy'):
        proxy = profile_info['data']['raw_proxy']
        ip = proxy.split(':')[0]
        try:
            response = requests.get(f"https://ipinfo.io/{ip}/json")
            if response.status_code == 200:
                data = response.json()
                return data.get("country", "Unknown")
        except requests.RequestException as e:
            print(f"Request to ipinfo.io failed: {e}")
    return "Unknown"
