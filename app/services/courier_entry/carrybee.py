import httpx
from app.services.fraud_check.carrybee import CarrybeeChecker

class CarrybeeEntry:
    def __init__(self, creds: dict):
        self.base_url = creds.get('base_url') or 'https://api-merchant.carrybee.com/'
        if not self.base_url.endswith('/'):
            self.base_url += '/'
            
        self.client_id = creds.get('client_id') or ''
        self.client_secret = creds.get('client_secret') or ''
        self.client_context = creds.get('client_context') or ''
        self.store_id = creds.get('store_id') or ''
        
        # Default choices
        self.delivery_type = 1
        self.product_type = 1
        self.item_weight = 200
        self.item_quantity = 1

    def _get_headers(self):
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Client-Id": self.client_id,
            "Client-Secret": self.client_secret,
            "Client-Context": self.client_context
        }

    async def parse_address(self, query: str):
        # Enforce Carrybee's minimum length requirement
        if len(query) < 10:
            query = query + " Bangladesh"
        
        # We use the native merchant login for the parser now, due to "Hub coverage not found" on public API headers
        checker = CarrybeeChecker()
        token = await checker._get_token()
        if not token:
            return None, None, "CarryBee merchant login failed (check .env credentials)"
            
        url = f"https://api-merchant.carrybee.com/api/v2/businesses/{checker.business_id}/address-parser"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://merchant.carrybee.com",
            "Referer": "https://merchant.carrybee.com/"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"query": query}, headers=headers)
            
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("error") and data.get("data"):
                    return data["data"].get("city_id"), data["data"].get("zone_id"), None
                return None, None, f"Parse internal error: {data}"
                
            return None, None, f"HTTP {resp.status_code}: {resp.text}"

    async def create_parcel(self, data: dict, merchant_order_id: str) -> dict:
        url = f"{self.base_url}api/v2/orders"
        city_id = data.get("city_id")
        zone_id = data.get("zone_id")
        
        parse_err = None
        if not city_id or not zone_id:
            p_city, p_zone, parse_err = await self.parse_address(data["recipient_address"])
            city_id = city_id or p_city
            zone_id = zone_id or p_zone

        payload = {
            "store_id": str(self.store_id),
            "merchant_order_id": merchant_order_id,
            "delivery_type": self.delivery_type,
            "product_type": self.product_type,
            "recipient_name": data["recipient_name"],
            "recipient_phone": data["recipient_phone"],
            "recipient_address": data["recipient_address"],
            "city_id": city_id,
            "zone_id": zone_id,
            "item_weight": self.item_weight,
            "item_quantity": self.item_quantity,
            "collectable_amount": int(data["cod_amount"])
        }
        
        if not city_id or not zone_id:
             return {
                "success": False,
                "courier": "carrybee",
                "message": f"Auto-parser failed resolving Zone. DBbg: {parse_err} | Endpoint: api/v2/businesses/{self.store_id}/address-parser",
                "raw_response": {"error": "Parser failed"}
             }

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=self._get_headers())
            try:
                resp_data = resp.json()
            except:
                resp_data = {"error": f"HTTP {resp.status_code}", "body": resp.text}
                
            if resp.status_code in [200, 201, 202] and not resp_data.get('error'):
                data_block = resp_data.get("data", {})
                extracted_consignment = data_block.get("consignment_id") or resp_data.get("consignment_id")
                
                # Carrybee might process asynchronously and not give the ID outright. Let's fetch it explicitly using the internal Merchant Tracking ID we just assigned!
                if not extracted_consignment:
                    fetch_url = f"{self.base_url}api/v2/orders/{merchant_order_id}/details"
                    async with httpx.AsyncClient() as get_client:
                        details_resp = await get_client.get(fetch_url, headers=self._get_headers())
                        if details_resp.status_code == 200:
                            det_data = details_resp.json()
                            if not det_data.get('error') and det_data.get('data'):
                                extracted_consignment = det_data['data'].get('consignment_id')

                return {
                    "success": True,
                    "merchant_order_id": merchant_order_id,
                    "consignment_id": extracted_consignment,
                    "message": resp_data.get("message", "Order accepted to be processed"),
                    "courier": "carrybee",
                    "raw_response": resp_data
                }
                
            return {
                "success": False,
                "courier": "carrybee",
                "message": resp_data.get("message", f"Failed to create order (HTTP {resp.status_code})"),
                "raw_response": resp_data
            }

    async def get_cities(self):
        url = f"{self.base_url}api/v2/cities"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("error"):
                    return data.get("data", {}).get("cities", [])
        return []
        
    async def get_zones(self, city_id):
        url = f"{self.base_url}api/v2/cities/{city_id}/zones"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._get_headers())
            if resp.status_code == 200:
                data = resp.json()
                if not data.get("error"):
                    return data.get("data", {}).get("zones", [])
        return []
