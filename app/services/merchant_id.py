from pymongo import ReturnDocument
from app.database import db

async def get_next_merchant_id(business_name: str) -> str:
    """Atomically increment and return next merchant order ID."""
    result = await db.merchant_id_counters.find_one_and_update(
        {"business_name": business_name},
        {"$inc": {"current_number": 1}},
        return_document=ReturnDocument.AFTER
    )
    if not result:
        raise ValueError(f"No merchant ID counter for business: {business_name}")
    return f"{result['prefix']}{result['current_number']}"

async def rollback_merchant_id(business_name: str):
    """Atomically decrement the merchant ID counter if tracking creation fails."""
    await db.merchant_id_counters.update_one(
        {"business_name": business_name},
        {"$inc": {"current_number": -1}}
    )

async def create_business_counter(business_name: str, prefix: str, starting_number: int = 0):
    """Create a new counter for a business."""
    # Check if exists
    existing = await db.merchant_id_counters.find_one({"business_name": business_name})
    if existing:
        return {"error": "Business counter already exists"}
        
    await db.merchant_id_counters.insert_one({
        "business_name": business_name,
        "prefix": prefix,
        "current_number": starting_number,
        "created_at": datetime.utcnow().isoformat()
    })
    return {"success": True, "business": business_name, "prefix": prefix}
