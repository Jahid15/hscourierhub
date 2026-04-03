from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_current_user_optional
from app.models.parcel import ParcelCreateRequest, ParcelCreateResponse
from app.services.courier_entry.manager import CourierEntryManager
from app.services.courier_entry.carrybee import CarrybeeEntry
from app.services.courier_entry.pathao import PathaoEntry
from app.database import db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
manager = CourierEntryManager()

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
