from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.auth import get_current_user
from app.database import db
from app.services.merchant_id import get_next_merchant_id
from datetime import datetime

router = APIRouter(tags=["Merchant ID"])

class CreateBusinessRequest(BaseModel):
    business_name: str
    prefix: str
    starting_number: int = 0

class CourierProfileRequest(BaseModel):
    business_name: str
    courier: str
    credentials: dict

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from app.auth import get_current_user_optional

templates = Jinja2Templates(directory="app/templates")

@router.get("/merchant-ids", response_class=HTMLResponse)
async def merchant_id_page(request: Request, user: dict = Depends(get_current_user_optional)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("merchant_ids.html", {"request": request, "title": "Merchant IDs"})

@router.get("/api/v1/merchant-id")
async def get_merchant_id(business: str = Query(..., description="Business name"), user: dict = Depends(get_current_user)):
    counter = await db.merchant_id_counters.find_one({"business_name": business})
    if not counter:
        raise HTTPException(status_code=404, detail="Business not found")
        
    return {
        "prefix": counter["prefix"],
        "number": counter["current_number"],
        "full_id": f"{counter['prefix']}{counter['current_number']}"
    }

@router.post("/api/v1/merchant-id")
async def generate_next_merchant_id(business: str = Query(..., description="Business name"), user: dict = Depends(get_current_user)):
    try:
        new_id = await get_next_merchant_id(business)
        return {"full_id": new_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/api/v1/merchant-id/create-business")
async def create_business(data: CreateBusinessRequest, user: dict = Depends(get_current_user)):
    existing = await db.merchant_id_counters.find_one({"business_name": data.business_name})
    if existing:
        raise HTTPException(status_code=400, detail="Business counter already exists")
        
    await db.merchant_id_counters.insert_one({
        "business_name": data.business_name,
        "prefix": data.prefix,
        "current_number": data.starting_number,
        "created_at": datetime.utcnow().isoformat()
    })
    return {"success": True, "business": data.business_name, "prefix": data.prefix}

@router.get("/api/v1/merchant-id/all")
async def get_all_businesses(user: dict = Depends(get_current_user)):
    counters = await db.merchant_id_counters.find().to_list(None)
    for c in counters:
        c["_id"] = str(c["_id"])
    return {"success": True, "data": counters}

@router.put("/api/v1/merchant-id/{business_id}")
async def update_business(business_id: str, data: CreateBusinessRequest, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    try:
        obj_id = ObjectId(business_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    await db.merchant_id_counters.update_one(
        {"_id": obj_id},
        {"$set": {
            "business_name": data.business_name,
            "prefix": data.prefix,
            "current_number": data.starting_number
        }}
    )
    return {"success": True}

@router.delete("/api/v1/merchant-id/{business_id}")
async def delete_business(business_id: str, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    try:
        obj_id = ObjectId(business_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    await db.merchant_id_counters.delete_one({"_id": obj_id})
    return {"success": True}

# ----------------- COURIER CONFIGURATIONS -----------------

@router.get("/api/v1/courier-profiles")
async def get_courier_profiles(user: dict = Depends(get_current_user)):
    profiles = await db.courier_entry_profiles.find().to_list(None)
    for p in profiles:
        p["_id"] = str(p["_id"])
    return {"success": True, "data": profiles}

@router.post("/api/v1/courier-profiles")
async def create_courier_profile(data: CourierProfileRequest, user: dict = Depends(get_current_user)):
    await db.courier_entry_profiles.insert_one({
        "business_name": data.business_name,
        "courier": data.courier,
        "credentials": data.credentials,
        "created_at": datetime.utcnow().isoformat()
    })
    return {"success": True}

@router.put("/api/v1/courier-profiles/{profile_id}")
async def update_courier_profile(profile_id: str, data: CourierProfileRequest, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    try:
        obj_id = ObjectId(profile_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    await db.courier_entry_profiles.update_one(
        {"_id": obj_id},
        {"$set": {
            "business_name": data.business_name,
            "courier": data.courier,
            "credentials": data.credentials
        }}
    )
    return {"success": True}

@router.delete("/api/v1/courier-profiles/{profile_id}")
async def delete_courier_profile(profile_id: str, user: dict = Depends(get_current_user)):
    from bson import ObjectId
    try:
        obj_id = ObjectId(profile_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    await db.courier_entry_profiles.delete_one({"_id": obj_id})
    return {"success": True}
