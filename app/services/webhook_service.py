from app.database import db
from datetime import datetime

class WebhookService:
    @staticmethod
    async def process_steadfast(payload: dict):
        # Log webhook
        await db.webhook_logs.insert_one({
            "courier": "steadfast",
            "consignment_id": payload.get("consignment_id"),
            "payload": payload,
            "processed": False,
            "received_at": datetime.utcnow().isoformat()
        })
        
        # Look up parcel
        consignment_id = payload.get("consignment_id")
        status = payload.get("status")
        if consignment_id and status:
            await db.parcels.update_one(
                {"consignment_id": str(consignment_id)},
                {
                    "$set": {"status": status, "updated_at": datetime.utcnow().isoformat()},
                    "$push": {
                        "status_history": {"status": status, "timestamp": datetime.utcnow().isoformat(), "raw": payload}
                    }
                }
            )

    @staticmethod
    async def process_pathao(payload: dict):
        # Similar logic
        consignment_id = payload.get("consignment_id")
        status = payload.get("order_status")
        await db.webhook_logs.insert_one({
            "courier": "pathao",
            "consignment_id": consignment_id,
            "payload": payload,
            "processed": True,
            "received_at": datetime.utcnow().isoformat()
        })
        if consignment_id and status:
            await db.parcels.update_one(
                {"consignment_id": consignment_id},
                {
                    "$set": {"status": status, "updated_at": datetime.utcnow().isoformat()},
                    "$push": {"status_history": {"status": status, "timestamp": datetime.utcnow().isoformat(), "raw": payload}}
                }
            )

    @staticmethod
    async def process_carrybee(payload: dict):
        consignment_id = payload.get("consignment_id")
        status = payload.get("transfer_status")
        await db.webhook_logs.insert_one({
            "courier": "carrybee",
            "consignment_id": consignment_id,
            "payload": payload,
            "processed": True,
            "received_at": datetime.utcnow().isoformat()
        })
        if consignment_id and status:
            await db.parcels.update_one(
                {"consignment_id": consignment_id},
                {
                    "$set": {"status": status, "updated_at": datetime.utcnow().isoformat()},
                    "$push": {"status_history": {"status": status, "timestamp": datetime.utcnow().isoformat(), "raw": payload}}
                }
            )
