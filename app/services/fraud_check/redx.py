import httpx
from app.config import settings
import json

_REDX_TOKEN_CACHE = None

class RedXChecker:
    def __init__(self):
        self.api_base = "https://api.redx.com.bd"
        self.web_api_base = "https://redx.com.bd/api/redx_se"
        self.phone = settings.redx_merchant_phone 
        self.password = settings.redx_merchant_password
        self.shop_id = "394045"

    async def check(self, phone: str) -> dict:
        if not self.phone or not self.password:
            return {"error": "RedX credentials not found"}
            
        async with httpx.AsyncClient() as client:
            # 1. Login to get token and set session cookies
            login_url = f"{self.api_base}/v4/auth/login"
            payload = {
                "phone": f"88{self.phone}" if not self.phone.startswith("88") else self.phone,
                "password": self.password
            }
            headers = {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1",
                "Origin": "https://redx.com.bd",
                "Referer": "https://redx.com.bd/"
            }
            
            global _REDX_TOKEN_CACHE
            token = _REDX_TOKEN_CACHE

            if not token:
                try:
                    resp = await client.post(login_url, json=payload, headers=headers)
                    if resp.status_code != 200:
                        return {"error": f"RedX login failed [{resp.status_code}]: {resp.text}"}
                    data = resp.json().get("data", {})
                    token = data.get("accessToken")
                    _REDX_TOKEN_CACHE = token
                except Exception as e:
                    return {"error": f"RedX login exception: {e}"}
                    
                if not token:
                    return {"error": "RedX login failed (no token)"}

            # 2. Perform stats check
            formatted_phone = phone
            if not formatted_phone.startswith("880"):
                if formatted_phone.startswith("0"):
                    formatted_phone = "88" + formatted_phone
                elif not formatted_phone.startswith("+88"):
                    formatted_phone = "880" + formatted_phone
            formatted_phone = formatted_phone.replace("+", "")

            url = f"{self.web_api_base}/admin/parcel/customer-success-return-rate"
            params = {"phoneNumber": formatted_phone}
            
            headers.update({
                "x-access-token": f"Bearer {token}",
                "Authorization": f"Bearer {token}"
            })
            
            try:
                check_resp = await client.get(url, params=params, headers=headers)
                if check_resp.status_code == 200:
                    return check_resp.json()
                elif check_resp.status_code == 401 or check_resp.status_code == 403:
                     # Token expired or invalid, clear Cache for next run
                     _REDX_TOKEN_CACHE = None
                     return {"error": f"RedX token expired or invalid, will refresh on next search. Status: {check_resp.status_code}"}
                return {"error": f"Failed with status: {check_resp.status_code}"}
            except Exception as e:
                return {"error": str(e)}
