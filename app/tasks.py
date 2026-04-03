import asyncio
from datetime import datetime, timedelta
from app.database import db

async def daily_reset_loop():
    """
    Background daemon running infinitely while Uvicorn server is online.
    Checks exactly once a minute if the BD Time (UTC+6) is exactly or past 10:00 AM.
    If so, it runs the steadfast counter reset protocol once per day.
    """
    while True:
        try:
            # Bangladesh is UTC+6
            now_utc = datetime.utcnow()
            
            # Simple conversion to BD Time
            now_bd = now_utc + timedelta(hours=6)
            
            # Formulate current day string for tracker (e.g. "2026-04-03")
            current_day_str = now_bd.strftime("%Y-%m-%d")
            
            # It should trigger if current BD Time is exactly at or past 12:40 AM (00:40)
            minutes_since_midnight = now_bd.hour * 60 + now_bd.minute
            if minutes_since_midnight >= 40:
                # Check DB lock so we don't trigger multiple times today
                tracker = await db.app_settings.find_one({"_id": "scheduled_reset_tracker"})
                
                last_reset_day = tracker.get("last_date", "") if tracker else ""
                
                if last_reset_day != current_day_str:
                    # Execute Full Reset!
                    await db.steadfast_check_accounts.update_many(
                        {},
                        {"$set": {"consignment_current": 0, "fraud_current": 0, "status_login": "ok", "status_consignment": "active", "status_fraud": "active", "last_reset": now_utc.isoformat()}}
                    )
                    
                    # Update DB lock
                    await db.app_settings.update_one(
                        {"_id": "scheduled_reset_tracker"},
                        {"$set": {"last_date": current_day_str, "executed_at": now_utc.isoformat()}},
                        upsert=True
                    )
                    
                    print(f"[DAEMON] Steadfast usage limits automatically reset for the day! (BD Time: {now_bd})")
        
        except Exception as e:
            print(f"[DAEMON] Critical execution error in reset loop: {e}")
            
        # Sleep for exactly 60 seconds before waking up to check clock again
        await asyncio.sleep(60)
