import httpx
from app.config import settings

class CarrybeeChecker:
    def __init__(self):
        self.auth_url = "https://merchant.carrybee.com/api/auth"
        self.base_url = "https://api-merchant.carrybee.com/api/v2"
        self.phone = settings.carrybee_merchant_phone
        self.password = settings.carrybee_merchant_password
        self.business_id = settings.carrybee_business_id

    async def _get_token(self) -> str:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
            "Origin": "https://merchant.carrybee.com",
            "Referer": "https://merchant.carrybee.com/"
        }
        try:
            async with httpx.AsyncClient() as client:
                # 1. CSRF
                csrf_resp = await client.get(f"{self.auth_url}/csrf", headers=headers)
                if csrf_resp.status_code != 200:
                    return None
                csrf_token = csrf_resp.json().get('csrfToken')
                if not csrf_token:
                    return None

                # 2. Login
                phone_with_prefix = self.phone
                if not phone_with_prefix.startswith("+88"):
                    if phone_with_prefix.startswith("0"):
                        phone_with_prefix = "+88" + phone_with_prefix
                    else:
                        phone_with_prefix = "+880" + phone_with_prefix

                login_payload = {
                    "phone": phone_with_prefix,
                    "password": self.password,
                    "csrfToken": csrf_token,
                    "callbackUrl": "https://merchant.carrybee.com/login",
                    "json": "true"
                }
                
                login_resp = await client.post(
                    f"{self.auth_url}/callback/login?", 
                    data=login_payload,
                    headers={**headers, "Content-Type": "application/x-www-form-urlencoded"}
                )
                if login_resp.status_code not in [200, 302, 307]:
                    return None

                # 3. Session
                session_resp = await client.get(f"{self.auth_url}/session", headers=headers)
                if session_resp.status_code == 200:
                    data = session_resp.json()
                    user = data.get('user', {})
                    # optionally update business_id
                    if 'selectedBusinessId' in user:
                        self.business_id = user['selectedBusinessId']
                    return data.get('accessToken')
        except Exception as e:
            print(f"Carrybee token error: {e}")
        return None

    async def check(self, phone: str) -> dict:
        if not self.phone or not self.password:
            return {"error": "Carrybee credentials not configured"}
            
        token = await self._get_token()
        if not token:
            return {"error": "Carrybee login failed"}

        formatted_phone = phone
        if not formatted_phone.startswith("880"):
            if formatted_phone.startswith("0"):
                formatted_phone = "88" + formatted_phone
            elif not formatted_phone.startswith("+88"):
                formatted_phone = "880" + formatted_phone
        formatted_phone = formatted_phone.replace("+", "")

        url = f"{self.base_url}/businesses/{self.business_id}/customers/+{formatted_phone}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
            "Origin": "https://merchant.carrybee.com",
            "Referer": "https://merchant.carrybee.com/"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return resp.json()
                elif resp.status_code == 404:
                    try:
                        err_data = resp.json()
                        if "not found" in str(err_data.get("message", "")).lower():
                            return {"data": {
                                "total_order": 0,
                                "cancelled_order": 0,
                                "success_rate": 0,
                                "name": "Normal Customer"
                            }}
                    except Exception:
                        pass
                return {"error": f"Failed with status: {resp.status_code}"}
        except Exception as e:
            return {"error": str(e)}
