import datetime
from fastapi import APIRouter, Request, Response, BackgroundTasks
from app.database import db

router = APIRouter(tags=["Webhooks"])

async def process_webhook(courier: str, payload: dict, consignment_id, merchant_order_id, event_status: str):
    if not consignment_id and not merchant_order_id:
        return
        
    query = []
    if consignment_id:
        query.append({"consignment_id": consignment_id})
        query.append({"consignment_id": str(consignment_id)})
        if str(consignment_id).isdigit():
            query.append({"consignment_id": int(consignment_id)})
            
    if merchant_order_id:
        query.append({"merchant_order_id": merchant_order_id})
        query.append({"merchant_order_id": str(merchant_order_id)})
        
    parcel = await db.parcels.find_one({"$or": query})
    if not parcel:
        return

    # Create history entry
    hist_entry = {
        "status": event_status,
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "raw": payload
    }
    
    # Push to history
    await db.parcels.update_one(
        {"_id": parcel["_id"]},
        {
            "$push": {"status_history": hist_entry},
            "$set": {
                "status": event_status,
                "updated_at": hist_entry["timestamp"]
            }
        }
    )

@router.post("/api/v1/webhooks/steadfast")
async def steadfast_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Steadfast webhook handler.
    Expects standard POST with notification_type and status.
    Must return HTTP 200 OK with success JSON.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid JSON"}
        
    consignment_id = payload.get("consignment_id")
    event_status = payload.get("status", "unknown")
    
    background_tasks.add_task(process_webhook, "steadfast", payload, consignment_id, payload.get("invoice"), event_status.title())
    return {"status": "success", "message": "Webhook received successfully."}

@router.post("/api/v1/webhooks/carrybee")
async def carrybee_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Carrybee webhook handler.
    Handles the webhook.integration verification handshake (requires HTTP 202 and a specific header).
    Otherwise, tracks order.* events.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error", "message": "Invalid payload"}
        
    event = payload.get("event", "")
    
    # Required Challenge Handshake
    if event == "webhook.integration":
        res = Response(status_code=202)
        res.headers["X-CB-Webhook-Integration-Header"] = "40489fe0-9386-4fc9-8e92-2b2fcb9d451c"
        return res
        
    consignment_id = payload.get("consignment_id")
    merchant_order_id = payload.get("merchant_order_id")
    
    # Clean up the exact event verb into a human readable status
    status_str = event.replace("order.", "").replace("-", " ").title()
    if status_str.strip() == "":
        status_str = "Update Received"
        
    background_tasks.add_task(process_webhook, "carrybee", payload, consignment_id, merchant_order_id, status_str)
    
    return {"status": "success"}

@router.post("/api/v1/webhooks/pathao")
async def pathao_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Pathao webhook handler.
    Handles the webhook_integration handshake (requires HTTP 202 and specific header).
    Otherwise tracks order.* events.
    """
    try:
        payload = await request.json()
    except Exception:
        return {"status": "error"}
        
    event = payload.get("event", "")
    
    # Required Challenge Handshake
    if event == "webhook_integration":
        res = Response(status_code=202)
        res.headers["X-Pathao-Merchant-Webhook-Integration-Secret"] = "f3992ecc-59da-4cbe-a049-a13da2018d51"
        return res
        
    consignment_id = payload.get("consignment_id")
    merchant_order_id = payload.get("merchant_order_id")
    if not merchant_order_id:
        merchant_order_id = payload.get("Merchant Order ID (Optional)")
    
    status_str = event.replace("order.", "").replace("_", " ").replace("-", " ").title()
    if status_str.strip() == "":
        status_str = "Update Received"
        
    background_tasks.add_task(process_webhook, "pathao", payload, consignment_id, merchant_order_id, status_str)
    
    return {"status": "success"}
