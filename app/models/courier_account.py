from pydantic import BaseModel
from typing import Optional, Dict

class SteadfastAccountCreate(BaseModel):
    email: str
    password: str
    consignment_limit: int = 10
    fraud_limit: int = 5

class SteadfastAccountUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    consignment_limit: Optional[int] = None
    fraud_limit: Optional[int] = None
    status_login: Optional[str] = None
    status_consignment: Optional[str] = None
    status_fraud: Optional[str] = None

class CourierEntryAccountCreate(BaseModel):
    courier: str
    business_name: str
    account_name: str
    credentials: Dict[str, str]

class CourierEntryAccountUpdate(BaseModel):
    business_name: Optional[str] = None
    account_name: Optional[str] = None
    credentials: Optional[Dict[str, str]] = None
    is_active: Optional[bool] = None
