from pydantic import BaseModel
from typing import Any

class WebhookPayload(BaseModel):
    # Depending on courier, structure varies. We can accept generic dict.
    pass
    # But usually FastAPI accepts Request directly or Dict[str, Any]
    # So we might not heavily use this model for the payload itself since we will use RequestBody or Dict
