from app.services.courier_entry.steadfast import SteadfastEntry
from app.services.courier_entry.pathao import PathaoEntry
from app.services.courier_entry.carrybee import CarrybeeEntry
from app.services.merchant_id import get_next_merchant_id, rollback_merchant_id
from app.database import db
from datetime import datetime
from app.services.phone_utils import normalize_phone

class CourierEntryManager:
    def __init__(self):
        pass

    async def create_parcel(self, data: dict) -> dict:
        normalized_phone = normalize_phone(data["recipient_phone"])
        data["recipient_phone"] = normalized_phone
        
        business_name = data["business"]
        
        # 1. Generate Global Merchant Order ID for the Namespace
        try:
            merchant_order_id = await get_next_merchant_id(business_name)
        except ValueError as e:
            return {"success": False, "message": str(e), "error_code": "MERCHANT_ID_ERROR"}
            
        courier = data.get("courier", "").lower()
        
        # 2. Extract specific Courier Credentials for this business
        profile = await db.courier_entry_profiles.find_one({"business_name": business_name, "courier": courier})
        if not profile:
            return {"success": False, "message": f"Integration {business_name}-{courier} not configured.", "error_code": "PROFILE_NOT_FOUND"}
            
        creds = profile.get("credentials", {})
        
        # 3. Match and dynamically instantiate specific profile
        if courier == "steadfast":
            result = await SteadfastEntry(creds).create_parcel(data, merchant_order_id)
        elif courier == "pathao":
            result = await PathaoEntry(creds).create_parcel(data, merchant_order_id)
        elif courier == "carrybee":
            result = await CarrybeeEntry(creds).create_parcel(data, merchant_order_id)
        else:
            await rollback_merchant_id(business_name)
            return {"success": False, "message": f"Unknown courier: {courier}", "error_code": "COURIER_NOT_FOUND"}
            
        # 4. Handle Merchant ID Rollback if Courier rejected it
        if not result.get("success"):
            await rollback_merchant_id(business_name)
            
        # 3. Save to database if successful or even if failed (to keep history)
        if result.get("success"):
            parcel_doc = {
                "merchant_order_id": merchant_order_id,
                "business_name": data["business"],
                "courier": courier,
                "recipient_name": data["recipient_name"],
                "recipient_phone": data["recipient_phone"],
                "recipient_address": data["recipient_address"],
                "cod_amount": data["cod_amount"],
                "consignment_id": result.get("consignment_id"),
                "tracking_code": result.get("tracking_code"),
                "delivery_fee": result.get("delivery_fee"),
                "status": "pending",
                "courier_response": result.get("raw_response"),
                "status_history": [{"status": "pending", "timestamp": datetime.utcnow().isoformat(), "raw": result.get("raw_response")}],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            await db.parcels.insert_one(parcel_doc)

        return result
