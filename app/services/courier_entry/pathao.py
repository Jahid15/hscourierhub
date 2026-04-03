import httpx
import json

class PathaoEntry:
    def __init__(self, creds: dict):
        self.base_url = creds.get('base_url') or 'https://api-hermes.pathao.com'
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
            
        self.client_id = creds.get('client_id') or ''
        self.client_secret = creds.get('client_secret') or ''
        self.username = creds.get('username') or ''
        self.password = creds.get('password') or ''
        self.store_id = creds.get('store_id') or ''

    async def get_token(self) -> str:
        url = f"{self.base_url}/aladdin/api/v1/issue-token"
        payload = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "password",
            "username": self.username,
            "password": self.password
        }
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload)
                if resp.status_code == 200:
                    return resp.json().get('access_token')
            except:
                pass
        return None

    async def create_parcel(self, data: dict, merchant_order_id: str) -> dict:
        token = await self.get_token()
        if not token:
            return {"success": False, "message": "Failed to get Pathao token", "courier": "pathao"}
            
        url = f"{self.base_url}/aladdin/api/v1/orders"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "store_id": self.store_id,
            "merchant_order_id": merchant_order_id,
            "sender_name": "",
            "sender_phone": "",
            "recipient_name": data["recipient_name"],
            "recipient_phone": data["recipient_phone"],
            "recipient_address": data["recipient_address"],
            "recipient_city": data.get("city_id"),
            "recipient_zone": data.get("zone_id"),
            "recipient_area": data.get("area_id"),
            "delivery_type": 48, # Normal
            "item_type": 2, # Parcel
            "special_instruction": "",
            "item_quantity": 1,
            "item_weight": 0.5,
            "amount_to_collect": int(data["cod_amount"]),
            "item_description": ""
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp_data = resp.json() if resp.status_code in [200, 422] else {"error": f"HTTP {resp.status_code}", "body": resp.text}
            
            if resp.status_code == 200 and resp_data.get('type') == 'success':
                res_data = resp_data.get('data', {})
                return {
                    "success": True,
                    "merchant_order_id": merchant_order_id,
                    "consignment_id": res_data.get("consignment_id"),
                    "tracking_code": res_data.get("consignment_id"),
                    "delivery_fee": res_data.get("delivery_fee"),
                    "courier": "pathao",
                    "message": "Order Created Successfully",
                    "raw_response": resp_data
                }
            return {
                "success": False,
                "courier": "pathao",
                "message": resp_data.get("message", "Failed to create order"),
                "raw_response": resp_data
            }

    async def get_cities(self):
        token = await self.get_token()
        if not token:
            return []
        url = f"{self.base_url}/aladdin/api/v1/city-list"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                return resp.json().get('data', {}).get('data', [])
        return []
        
    async def get_zones(self, city_id):
        token = await self.get_token()
        url = f"{self.base_url}/aladdin/api/v1/cities/{city_id}/zone-list"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                return resp.json().get('data', {}).get('data', [])
        return []

    async def get_areas(self, zone_id):
        token = await self.get_token()
        url = f"{self.base_url}/aladdin/api/v1/zones/{zone_id}/area-list"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                return resp.json().get('data', {}).get('data', [])
        return []
