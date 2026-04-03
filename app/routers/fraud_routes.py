from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.auth import get_current_user, get_current_user_optional
from app.services.fraud_check.manager import FraudCheckManager
from app.models.fraud_check import FraudCheckResponse
from app.services.phone_utils import normalize_phone

router = APIRouter(tags=["Fraud Check"])
templates = Jinja2Templates(directory="app/templates")
fraud_manager = FraudCheckManager()

@router.get("/api/v1/fraud-check/{phone}", response_model=FraudCheckResponse)
@router.post("/api/v1/fraud-check/{phone}", response_model=FraudCheckResponse)
async def check_fraud_api(phone: str, bypass_cache: bool = False, user: dict = Depends(get_current_user)):
    """API endpoint for external consumption"""
    normalized_phone = normalize_phone(phone)
    return await fraud_manager.check_all(normalized_phone, bypass_cache=bypass_cache)

@router.get("/fraud-check", response_class=HTMLResponse)
async def fraud_check_page(request: Request, user: dict = Depends(get_current_user_optional)):
    if not user:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("fraud_check.html", {"request": request, "title": "Fraud Check"})
