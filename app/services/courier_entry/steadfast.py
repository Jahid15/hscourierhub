import httpx

class SteadfastEntry:
    def __init__(self, creds: dict):
        self.base_url = creds.get('base_url') or 'https://steadfast.com.bd/api/v1'
        if self.base_url.endswith('/'):
            self.base_url = self.base_url[:-1]
            
        self.api_key = creds.get('api_key') or ''
        self.secret_key = creds.get('secret_key') or ''

    async def create_parcel(self, data: dict, merchant_order_id: str) -> dict:
        url = f"{self.base_url}/create_order"
        headers = {
            "Api-Key": self.api_key,
            "Secret-Key": self.secret_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "invoice": merchant_order_id,
            "recipient_name": data["recipient_name"],
            "recipient_phone": data["recipient_phone"],
            "recipient_address": data["recipient_address"],
            "cod_amount": int(data["cod_amount"])
        }
        
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                resp_data = resp.json()
            except httpx.RequestError as e:
                return {"success": False, "courier": "steadfast", "message": f"Network Error: {str(e)}", "raw_response": {}}
            except httpx.HTTPStatusError as e:
                try:
                    resp_data = e.response.json()
                except:
                    resp_data = {"error": f"HTTP {e.response.status_code}", "body": e.response.text}
            except Exception as e:
                return {"success": False, "courier": "steadfast", "message": f"Unexpected Error: {str(e)}", "raw_response": {}}
            
            # Note: The api response format might vary.
            if resp.status_code == 200 and resp_data.get('status') == 200:
                consignment = resp_data.get('consignment', {})
                return {
                    "success": True,
                    "merchant_order_id": merchant_order_id,
                    "consignment_id": str(consignment.get("consignment_id")),
                    "tracking_code": consignment.get("tracking_code"),
                    "courier": "steadfast",
                    "message": "Order Created Successfully",
                    "raw_response": resp_data
                }
            return {
                "success": False,
                "courier": "steadfast",
                "message": resp_data.get("message", "Failed to create order"),
                "raw_response": resp_data
            }
