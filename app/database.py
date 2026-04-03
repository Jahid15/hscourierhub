from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

    def connect(self):
        try:
            if settings.mongodb_uri:
                self.client = AsyncIOMotorClient(settings.mongodb_uri)
                self.db = self.client[settings.mongodb_db_name]
                logger.info("Connected to MongoDB.")
            else:
                logger.warning("No MongoDB URI configured. Database operations will fail.")
        except Exception as e:
            logger.error(f"Error connecting to MongoDB: {e}")

    def disconnect(self):
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB.")

    # Property helpers to access collections
    @property
    def steadfast_check_accounts(self):
        return self.db.steadfast_check_accounts if self.db is not None else None

    @property
    def courier_entry_accounts(self):
        return self.db.courier_entry_accounts if self.db is not None else None

    @property
    def courier_entry_profiles(self):
        return self.db.courier_entry_profiles if self.db is not None else None

    @property
    def merchant_id_counters(self):
        return self.db.merchant_id_counters if self.db is not None else None

    @property
    def parcels(self):
        return self.db.parcels if self.db is not None else None

    @property
    def webhook_logs(self):
        return self.db.webhook_logs if self.db is not None else None

    @property
    def fraud_check_cache(self):
        return self.db.fraud_check_cache if self.db is not None else None

    @property
    def app_settings(self):
        return self.db.app_settings if self.db is not None else None

db = Database()
