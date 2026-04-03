import httpx
from app.config import settings

class PathaoChecker:
    def __init__(self):
        self.base_url = "https://merchant.pathao.com/api/v1"
        self.email = settings.pathao_username
        self.password = settings.pathao_password

    async def _get_token(self) -> str:
        url = f"{self.base_url}/login"
        payload = {"username": self.email, "password": self.password}
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://merchant.pathao.com",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
            "sec-ch-ua-platform": '\"iOS\"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                if "access_token" in data:
                    return data["access_token"]
                elif "token" in data:
                    return data["token"]
                elif "data" in data and isinstance(data["data"], dict):
                    return data["data"].get("access_token") or data["data"].get("token")
        return None

    async def check(self, phone: str) -> dict:
        if not self.email or not self.password:
            return {"error": "Pathao credentials not configured"}
            
        token = await self._get_token()
        if not token:
            return {"error": "Pathao login failed"}
            
        url = f"{self.base_url}/user/success"
        headers = {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "origin": "https://merchant.pathao.com",
            "user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
            "sec-ch-ua-platform": '\"iOS\"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "authorization": f"Bearer {token}"
        }
        payload = {"phone": phone}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, json=payload, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                return {"error": f"Failed with status: {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}
