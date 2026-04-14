from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_current_user_optional
from app.models.parcel import ParcelCreateRequest, ParcelCreateResponse
from app.services.courier_entry.manager import CourierEntryManager
from app.services.courier_entry.carrybee import CarrybeeEntry
from app.services.courier_entry.pathao import PathaoEntry
from app.database import db
from app.config import settings
from pydantic import BaseModel
import httpx
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
manager = CourierEntryManager()

class AIExtractRequest(BaseModel):
    text: str

@router.post("/api/v1/ai/extract", tags=["AI Tracking"])
async def extract_address_ai(data: AIExtractRequest, user: dict = Depends(get_current_user)):
    if not settings.openai_api_key:
        raise HTTPException(status_code=400, detail="OpenAI API Key not configured")
        
    prompt = f"""
Extract the customer details from the following raw text into a strict JSON format.
Make sure the JSON keys are EXACTLY: "name", "phone", "address", "cod_amount".
For cod_amount, just return the integer number (e.g. 1340).
If any field is missing, leave it as an empty string (or 0 for cod_amount).
Do NOT return markdown blocks (like ```json), ONLY output the raw JSON object.

Raw Text:
{data.text}
"""
    headers = {
        "Authorization": f"Bearer {settings.openai_api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(settings.openai_api_url, json=payload, headers=headers, timeout=15.0)
            resp.raise_for_status()
            res_data = resp.json()
            content = res_data["choices"][0]["message"]["content"].strip()
            
            # Clean possible markdown wrapping
            if content.startswith("```json"):
                content = content[7:]
            elif content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
                
            parsed = json.loads(content.strip())
            return {"success": True, "data": parsed}
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/parcel/create", response_model=ParcelCreateResponse, tags=["Parcel Entry"])
async def create_parcel_api(data: ParcelCreateRequest, user: dict = Depends(get_current_user)):
    result = await manager.create_parcel(data.model_dump())
    return result

@router.get("/api/v1/locations/cities", tags=["Locations"])
async def get_cities(courier: str = Query(...)):
    if courier.lower() == "carrybee":
        return await CarrybeeEntry().get_cities()
    elif courier.lower() == "pathao":
        return await PathaoEntry().get_cities()
    return []

@router.get("/api/v1/locations/zones", tags=["Locations"])
async def get_zones(courier: str = Query(...), city_id: int = Query(...)):
    if courier.lower() == "carrybee":
        return await CarrybeeEntry().get_zones(city_id)
    elif courier.lower() == "pathao":
        return await PathaoEntry().get_zones(city_id)
    return []

@router.get("/api/v1/locations/areas", tags=["Locations"])
async def get_areas(courier: str = Query(...), zone_id: int = Query(...)):
    if courier.lower() == "pathao":
        return await PathaoEntry().get_areas(zone_id)
    return []

@router.get("/parcel-entry", response_class=HTMLResponse)
async def parcel_entry_page(request: Request, user: dict = Depends(get_current_user_optional)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("parcel_entry.html", {"request": request, "title": "Parcel Entry"})

@router.get("/parcel-list", response_class=HTMLResponse)
async def parcel_list_page(request: Request, user: dict = Depends(get_current_user_optional)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("parcels.html", {"request": request, "title": "Parcel Tracking"})

@router.get("/api/v1/parcels", tags=["Parcel Tracking"])
async def get_all_parcels(skip: int = 0, limit: int = 100, user: dict = Depends(get_current_user)):
    parcels = await db.parcels.find().sort("created_at", -1).skip(skip).limit(limit).to_list(length=limit)
    for p in parcels:
        p["_id"] = str(p["_id"])
    return {"success": True, "data": parcels}

@router.get("/api/v1/parcels/{merchant_order_id}", tags=["Parcel Tracking"])
async def get_parcel_status(merchant_order_id: str, user: dict = Depends(get_current_user)):
    parcel = await db.parcels.find_one({"merchant_order_id": merchant_order_id})
    if not parcel:
        raise HTTPException(status_code=404, detail="Parcel not found")
    parcel["_id"] = str(parcel["_id"])
    return {"success": True, "data": parcel}
