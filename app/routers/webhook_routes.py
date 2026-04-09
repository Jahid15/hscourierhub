import datetime
import httpx
import logging
from fastapi import APIRouter, Request, Response, BackgroundTasks
from fastapi.responses import JSONResponse
from app.database import db
from app.config import settings

router = APIRouter(tags=["Webhooks"])

async def send_telegram_notification(parcel: dict, event_status: str, updated_at: str, payload_data: dict):
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return
        
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    
    # Extract any courier notes or reasons safely (e.g. tracking_message, note, reason)
    note_str = payload_data.get("reason", payload_data.get("tracking_message", payload_data.get("note", "")))
    note_block = f"""\n<b>Courier Note</b>: <i>{note_str}</i>\n""" if str(note_str).strip() else ""
    
    # Calculate amounts
    amount = parcel.get("cod_amount", 0)
    
    # Usually couriers don't send individual 'collected_amount' through simplistic webhooks on every status,
    # but we can do our best or default to 0 if not delivered.
    collected = amount if event_status.strip().lower() == "delivered" else 0
    
    # Build Consignment Link securely
    courier = str(parcel.get("courier", "")).lower()
    c_id = parcel.get('consignment_id', 'N/A')
    
    if courier == "pathao":
        c_link = f"https://merchant.pathao.com/courier/orders/{c_id}"
    elif courier == "carrybee":
        b_id = parcel.get("business_id", "1490")
        c_link = f"https://merchant.carrybee.com/businesses/{b_id}/orders/{c_id}"
    elif courier == "steadfast":
        c_link = f"https://steadfast.com.bd/user/consignment/{c_id}"
    else:
        c_link = f"https://hscourierhub.onrender.com/parcel-list"

    if c_id != "N/A":
        consignment_display = f'<a href="{c_link}">{c_id}</a>'
    else:
        consignment_display = "N/A"
        
    phone = str(parcel.get('recipient_phone', 'N/A')).replace(" ", "").strip()
    # To force telegram to recognize Bangladeshi local numbers, we append +88 if missing and output raw string natively
    if phone.startswith("01") and len(phone) == 11:
        phone = f"+88{phone}"

    msg = f"""📦 <b>Parcel Update [{event_status}]</b>
{note_block}
<b>Consignment </b> : {consignment_display}
<b>Order ID    </b> : {parcel.get('merchant_order_id', 'N/A')}
<b>Status      </b> : {event_status}
<b>Updated At  </b> : {updated_at}
<b>Amount      </b> : ৳{amount}
<b>Collected   </b> : ৳{collected}

━━━ Customer Details ━━━
<b>Name        </b> : {parcel.get('recipient_name', 'N/A')}
<b>Phone       </b> : {phone}
<b>Address     </b> : {parcel.get('recipient_address', 'N/A')}"""

    telegram_payload = {
        "chat_id": settings.telegram_chat_id,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            await client.post(url, json=telegram_payload)
    except Exception as e:
        logging.getLogger(__name__).error(f"Telegram notification failed: {e}")

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
    hist_ts = datetime.datetime.utcnow().isoformat() + "Z"
    hist_entry = {
        "status": event_status,
        "timestamp": hist_ts,
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
    
    # Broadcast to Telegram
    dt_formatted = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await send_telegram_notification(parcel, event_status, dt_formatted, payload)

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
        # Fallback to pure body parse if JSON fails, since Pathao integration test sometimes sends malformed JSON
        raw_body = await request.body()
        import json
        try:
            payload = json.loads(raw_body)
        except json.JSONDecodeError:
            # If it's a completely corrupted test ping, manually scan for the generic event string
            if b'webhook_integration' in raw_body:
                payload = {"event": "webhook_integration"}
            else:
                return {"status": "error"}
    except Exception:
        return {"status": "error"}
        
    event = payload.get("event", "")
    
    # Required Challenge Handshake
    if event == "webhook_integration":
        # Actively extract the secret if Pathao dynamically embeds it in the request headers during testing
        incoming_secret = request.headers.get("X-Pathao-Merchant-Webhook-Integration-Secret", "f3992ecc-59da-4cbe-a049-a13da2018d51")
        
        # Build pure explicit response format ensuring Uvicorn framework doesn't mangle Pathao's brittle verifier
        response = Response(content='{"status":"success"}', media_type="application/json", status_code=202)
        response.headers["X-Pathao-Merchant-Webhook-Integration-Secret"] = str(incoming_secret).strip()
        response.headers["X-PATHAO-Merchant-Webhook-Integration-Secret"] = str(incoming_secret).strip()
        
        return response
        
    consignment_id = payload.get("consignment_id")
    merchant_order_id = payload.get("merchant_order_id")
    if not merchant_order_id:
        merchant_order_id = payload.get("Merchant Order ID (Optional)")
    
    status_str = event.replace("order.", "").replace("_", " ").replace("-", " ").title()
    if status_str.strip() == "":
        status_str = "Update Received"
        
    background_tasks.add_task(process_webhook, "pathao", payload, consignment_id, merchant_order_id, status_str)
    
    return {"status": "success"}
