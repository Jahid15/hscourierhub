from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.services.webhook_service import WebhookService
from app.auth import get_current_user_optional, get_current_user
from app.database import db

router = APIRouter(tags=["Webhooks"])
templates = Jinja2Templates(directory="app/templates")

@router.post("/webhooks/steadfast")
async def steadfast_webhook(request: Request):
    payload = await request.json()
    await WebhookService.process_steadfast(payload)
    return {"status": "success"}

@router.post("/webhooks/pathao")
async def pathao_webhook(request: Request):
    payload = await request.json()
    await WebhookService.process_pathao(payload)
    return {"status": "success"}

@router.post("/webhooks/carrybee")
async def carrybee_webhook(request: Request):
    payload = await request.json()
    await WebhookService.process_carrybee(payload)
    return {"status": "success"}

# UI Routes
@router.get("/webhooks", response_class=HTMLResponse)
async def webhooks_page(request: Request, user: dict = Depends(get_current_user_optional)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("webhooks.html", {"request": request, "title": "Webhook Logs"})

@router.get("/api/v1/webhooks/logs")
async def get_webhook_logs(limit: int = 50, user: dict = Depends(get_current_user)):
    logs = await db.webhook_logs.find().sort("received_at", -1).limit(limit).to_list(None)
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs
