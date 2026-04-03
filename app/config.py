from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # App
    app_password: str = "admin123"
    app_secret_key: str = "change-me"
    session_expiry_days: int = 30
    external_api_key: str = ""

    # MongoDB
    mongodb_uri: str = ""
    mongodb_db_name: str = "hscourierhub"

    # Carrybee
    carrybee_base_url: str = "https://developers.carrybee.com/"
    carrybee_client_id: str = ""
    carrybee_client_secret: str = ""
    carrybee_client_context: str = ""
    carrybee_merchant_phone: str = ""
    carrybee_merchant_password: str = ""
    carrybee_business_id: int = 1490
    carrybee_store_id: str = "652"

    # Pathao
    pathao_base_url: str = "https://api-hermes.pathao.com"
    pathao_client_id: str = ""
    pathao_client_secret: str = ""
    pathao_username: str = ""
    pathao_password: str = ""
    pathao_store_id: int = 283694

    # RedX
    redx_merchant_phone: str = ""
    redx_merchant_password: str = ""

    # Steadfast
    steadfast_base_url: str = "https://portal.packzy.com/api/v1"
    steadfast_api_key: str = ""
    steadfast_secret_key: str = ""

    # OpenAI
    openai_api_key: str = ""
    openai_api_url: str = "https://api.openai.com/v1/chat/completions"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
