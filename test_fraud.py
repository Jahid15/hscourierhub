import asyncio
from app.services.fraud_check.manager import FraudCheckManager

async def test():
    manager = FraudCheckManager()
    resp = await manager.check_all("01676225090")
    print(resp.model_dump_json(indent=2))

asyncio.run(test())
