from pydantic import BaseModel
from typing import List, Optional, Any

class FraudCheckRequest(BaseModel):
    phone: str

class CourierResult(BaseModel):
    name: str
    total: int = 0
    delivered: int = 0
    cancelled: int = 0
    comment: Optional[str] = None
    status: str = "ok" # "ok" | "error" | "limit_reached"
    error_message: Optional[str] = None

class Summary(BaseModel):
    total_parcels: int = 0
    total_delivered: int = 0
    total_cancelled: int = 0
    steadfast_fraud_reports: int = 0
    overall_success_rate: float = 0.0
    customer_name: Optional[str] = None

class FraudCheckResponse(BaseModel):
    phone: str
    summary: Summary
    couriers: List[CourierResult]
    checked_at: str
    cached: bool = False
