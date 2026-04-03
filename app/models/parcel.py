from pydantic import BaseModel
from typing import Optional, Any

class ParcelCreateRequest(BaseModel):
    courier: str
    business: str
    recipient_name: str
    recipient_phone: str
    recipient_address: str
    cod_amount: float
    city_id: Optional[int] = None
    zone_id: Optional[int] = None
    area_id: Optional[int] = None

class ParcelCreateResponse(BaseModel):
    success: bool
    merchant_order_id: Optional[str] = None
    consignment_id: Optional[str] = None
    tracking_code: Optional[str] = None
    courier: str
    delivery_fee: Optional[float] = None
    cod_fee: Optional[float] = None
    message: str
    raw_response: Any = None
