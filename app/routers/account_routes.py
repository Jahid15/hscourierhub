from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_current_user_optional
from app.database import db
from app.models.courier_account import SteadfastAccountCreate, SteadfastAccountUpdate
from pydantic import BaseModel
from datetime import datetime
from bson import ObjectId

router = APIRouter(tags=["Account Management"])
templates = Jinja2Templates(directory="app/templates")

# --- UI Route ---
@router.get("/accounts", response_class=HTMLResponse)
async def accounts_page(request: Request, user: dict = Depends(get_current_user_optional)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("accounts.html", {"request": request, "title": "Account Management"})

# --- System Settings API ---
class CacheSetting(BaseModel):
    enabled: bool

@router.get("/api/v1/settings/cache")
async def get_cache_setting(user: dict = Depends(get_current_user)):
    setting = await db.app_settings.find_one({"_id": "cache_settings"})
    if not setting:
        return {"enabled": True}
    return {"enabled": setting.get("global_cache_enabled", True)}

@router.post("/api/v1/settings/cache")
async def update_cache_setting(data: CacheSetting, user: dict = Depends(get_current_user)):
    await db.app_settings.update_one(
        {"_id": "cache_settings"},
        {"$set": {"global_cache_enabled": data.enabled}},
        upsert=True
    )
    return {"success": True, "enabled": data.enabled}

# --- Steadfast Fraud Check Accounts API ---

@router.get("/api/v1/accounts/fraud-check")
async def list_steadfast_accounts(user: dict = Depends(get_current_user)):
    accounts = await db.steadfast_check_accounts.find().to_list(None)
    for acc in accounts:
        acc["id"] = str(acc.pop("_id"))
        # Mask password partially for safety
        pw = acc.get("password", "")
        if pw:
            acc["password"] = pw[:2] + "*" * (len(pw) - 2) if len(pw) > 2 else "***"
    return accounts

@router.post("/api/v1/accounts/fraud-check")
async def add_steadfast_account(data: SteadfastAccountCreate, user: dict = Depends(get_current_user)):
    doc = data.model_dump()
    doc.update({
        "consignment_current": 0,
        "fraud_current": 0,
        "status_login": "ok",
        "status_consignment": "active",
        "status_fraud": "active",
        "last_used": None,
        "last_reset": datetime.utcnow().isoformat(),
        "created_at": datetime.utcnow().isoformat()
    })
    result = await db.steadfast_check_accounts.insert_one(doc)
    return {"success": True, "id": str(result.inserted_id)}

@router.put("/api/v1/accounts/fraud-check/{account_id}")
async def update_steadfast_account(account_id: str, data: SteadfastAccountUpdate, user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        return {"success": True}
        
    # Unmasking logic protection: If a masked password is sent back, don't update it
    if "password" in update_data and "*" in update_data["password"]:
        del update_data["password"]
    
    result = await db.steadfast_check_accounts.update_one(
        {"_id": ObjectId(account_id)},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True}

@router.delete("/api/v1/accounts/fraud-check/{account_id}")
async def delete_steadfast_account(account_id: str, user: dict = Depends(get_current_user)):
    result = await db.steadfast_check_accounts.delete_one({"_id": ObjectId(account_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"success": True}

@router.post("/api/v1/accounts/fraud-check/reset-all")
async def reset_all_steadfast_usage(user: dict = Depends(get_current_user)):
    await db.steadfast_check_accounts.update_many(
        {},
        {"$set": {"consignment_current": 0, "fraud_current": 0, "status_login": "ok", "status_consignment": "active", "status_fraud": "active", "last_reset": datetime.utcnow().isoformat()}}
    )
    return {"success": True, "message": "All counters reset to 0"}
