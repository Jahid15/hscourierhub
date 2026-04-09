import httpx
from app.services.fraud_check.carrybee import CarrybeeChecker

class CarrybeeEntry:
    def __init__(self, creds: dict):
        base = creds.get('base_url') or 'https://developers.carrybee.com/'
        # Force correct developer API if legacy api-merchant is stored in DB
        if 'api-merchant' in base:
            base = 'https://developers.carrybee.com/'
            
        self.base_url = base if base.endswith('/') else base + '/'
            
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
            "Client-ID": self.client_id,
            "Client-Secret": self.client_secret,
            "Client-Context": self.client_context
        }

    async def parse_address(self, query: str):
        # Enforce Carrybee's minimum length requirement
        if len(query) < 10:
            query = query + " Bangladesh"
            
        url = f"{self.base_url}api/v2/address-details"

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.post(url, json={"query": query}, headers=self._get_headers())
                resp_data = resp.json()
            except httpx.RequestError as e:
                return None, None, f"Network Timeout / Reset executing Address Parser: {str(e)}"
            except Exception as e:
                return None, None, f"Unexpected Parser Crash: {str(e)}"
            
            if resp.status_code == 200:
                if not resp_data.get("error") and resp_data.get("data"):
                    city_id = resp_data["data"].get("city_id")
                    zone_id = resp_data["data"].get("zone_id")
                    
                    # Carrybee Global Parser sometimes evaluates text to legacy IDs (e.g. 1079/1082 for Uttara)
                    # which don't exist in live production Hub maps, triggering 'Hub coverage not found'.
                    if city_id and zone_id:
                        active_zones = await self.get_zones(city_id)
                        is_valid = any(z['id'] == zone_id for z in active_zones)
                        
                        if not is_valid and active_zones:
                            query_words = [w for w in query.replace(',', ' ').lower().split() if len(w) > 3]
                            for w in query_words:
                                match = next((z for z in active_zones if w in z['name'].lower()), None)
                                if match:
                                    zone_id = match['id']
                                    break
                                    
                    return city_id, zone_id, None
                
                # Handling 422 or logic errors elegantly
                cause = resp_data.get("message")
                if resp_data.get("causes"): cause += f" ({resp_data['causes']})"
                return None, None, f"Parser rejected query: {cause}"
                
            return None, None, f"HTTP {resp.status_code}: {resp_data.get('message', 'Unknown API Error')}"

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
                "message": f"Carrybee Address auto-parser failed resolving City/Zone. Details: {parse_err}",
                "raw_response": {"error": "Parser failed block", "details": parse_err}
             }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=self._get_headers())
                resp.raise_for_status()
                resp_data = resp.json()
            except httpx.RequestError as e:
                return {"success": False, "courier": "carrybee", "message": f"Network Error: {str(e)}", "raw_response": {}}
            except httpx.HTTPStatusError as e:
                try:
                    resp_data = e.response.json()
                except:
                    resp_data = {"error": f"HTTP {e.response.status_code}", "body": e.response.text}
            except Exception as e:
                return {"success": False, "courier": "carrybee", "message": f"Unexpected Error: {str(e)}", "raw_response": {}}
                
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
