import asyncio
from datetime import datetime, timedelta
from app.services.fraud_check.steadfast import SteadfastChecker
from app.services.fraud_check.pathao import PathaoChecker
from app.services.fraud_check.carrybee import CarrybeeChecker
from app.services.fraud_check.redx import RedXChecker
from app.models.fraud_check import FraudCheckResponse, CourierResult, Summary
from app.database import db

class FraudCheckManager:
    def __init__(self):
        self.steadfast = SteadfastChecker()
        self.pathao = PathaoChecker()
        self.carrybee = CarrybeeChecker()
        self.redx = RedXChecker()

    async def check_all(self, phone: str, bypass_cache: bool = False) -> FraudCheckResponse:
        # Check global cache state
        global_setting = await db.app_settings.find_one({"_id": "cache_settings"})
        global_cache_enabled = global_setting.get("global_cache_enabled", True) if global_setting else True

        # Check cache first
        if global_cache_enabled and not bypass_cache:
            cached = await db.fraud_check_cache.find_one({"phone": phone, "expires_at": {"$gt": datetime.utcnow().isoformat()}})
            if cached:
                results = cached["results"]
                results["cached"] = True
                return FraudCheckResponse(**results)

        # Run checks in parallel
        results = await asyncio.gather(
            self.steadfast.check(phone),
            self.pathao.check(phone),
            self.carrybee.check(phone),
            self.redx.check(phone)
        )

        steadfast_res, pathao_res, carrybee_res, redx_res = results
        
        couriers = []
        summary = Summary()

        # 1. Steadfast
        sf_result = CourierResult(name="Steadfast")
        if steadfast_res.get("data"):
            d = steadfast_res["data"]
            # Consignment metrics
            sf_result.total = int(d.get("total_delivered", 0)) + int(d.get("total_cancelled", 0))
            sf_result.delivered = int(d.get("total_delivered", 0))
            sf_result.cancelled = int(d.get("total_cancelled", 0))
            
            # Fetch fraud reports based on user's confirmed JSON: "frauds", handling list/null edgecases
            frauds_val = d.get("frauds", 0)
            if isinstance(frauds_val, list):
                fraud_count = len(frauds_val)
            else:
                fraud_count = int(frauds_val) if frauds_val else 0
            
            if fraud_count > 0:
                sf_result.comment = f"fraud: {fraud_count}"
                summary.steadfast_fraud_reports = fraud_count
        
        if steadfast_res.get("errors"):
            sf_result.status = "error"
            sf_result.error_message = "; ".join(steadfast_res["errors"])
        couriers.append(sf_result)

        # 2. Pathao
        pt_result = CourierResult(name="Pathao")
        if "data" in pathao_res:
            data = pathao_res["data"].get("customer", {})
            pt_result.delivered = int(data.get("successful_delivery", 0))
            pt_result.total = int(data.get("total_delivery", 0))
            pt_result.cancelled = pt_result.total - pt_result.delivered
            pt_result.comment = str(pathao_res["data"].get("customer_rating", "N/A")).replace("_", " ")
        else:
            pt_result.status = "error"
            pt_result.error_message = pathao_res.get("error", "Unknown error")
        couriers.append(pt_result)

        # 3. CarryBee
        cb_result = CourierResult(name="CarryBee")
        if "data" in carrybee_res:
            data = carrybee_res["data"]
            cb_result.total = int(data.get("total_order", 0))
            cb_result.cancelled = int(data.get("cancelled_order", 0))
            cb_result.delivered = cb_result.total - cb_result.cancelled
            
            customer_name = data.get("name") or data.get("customer_name") or data.get("customerName")
            if customer_name:
                cb_result.comment = f"Name: {customer_name} | Success rate: {data.get('success_rate')}%"
                summary.customer_name = str(customer_name)
            else:
                cb_result.comment = f"Success rate: {data.get('success_rate')}%"
        else:
            cb_result.status = "error"
            cb_result.error_message = carrybee_res.get("error", "Unknown error")
        couriers.append(cb_result)

        # 4. RedX
        rx_result = CourierResult(name="RedX")
        if "data" in redx_res:
            data = redx_res["data"]
            rx_result.total = int(data.get("totalParcels", 0))
            rx_result.delivered = int(data.get("deliveredParcels", 0))
            rx_result.cancelled = rx_result.total - rx_result.delivered
            rx_result.comment = str(data.get("customerSegment"))
        else:
            rx_result.status = "error"
            rx_result.error_message = redx_res.get("error", "Unknown error")
        couriers.append(rx_result)

        # Aggregate summary
        for c in couriers:
            if c.status == "ok":
                summary.total_parcels += c.total
                summary.total_delivered += c.delivered
                summary.total_cancelled += c.cancelled

        if summary.total_parcels > 0:
            summary.overall_success_rate = round((summary.total_delivered / summary.total_parcels) * 100, 2)

        response = FraudCheckResponse(
            phone=phone,
            summary=summary,
            couriers=couriers,
            checked_at=datetime.utcnow().isoformat(),
            cached=False
        )

        # Save to cache if globally enabled
        if global_cache_enabled:
            await db.fraud_check_cache.update_one(
                {"phone": phone},
                {"$set": {
                    "results": response.model_dump() if hasattr(response, "model_dump") else response.dict(),
                    "expires_at": (datetime.utcnow() + timedelta(days=5)).isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }},
                upsert=True
            )
        
        return response
