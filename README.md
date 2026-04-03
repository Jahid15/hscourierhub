# HelloSquare Courier Hub

Unified API engine for Fraud Checking and Courier Entry across multiple Bangladeshi couriers (Steadfast, Pathao, Carrybee, RedX).

## Features
1. **Universal Fraud Check:** Send a phone number, get aggregated delivery success/return rates across 4 major couriers.
2. **Unified Courier Entry:** Send parcel data to one endpoint, dynamically route to Steadfast, Pathao, or Carrybee.
3. **Smart Steadfast Rotation:** Automatically rotates through multiple Steadfast accounts to bypass rate limits (10 logic limit).
4. **API First:** Fully integrates with WooCommerce, Laravel, and custom apps.

## Tech Stack
- **Python 3.11+**
- **FastAPI**
- **MongoDB Atlas**
- **Jinja2 / Tailwind CSS**

## Running Locally

1. Create a `.env` file (copy from `.env.example`).
2. Set your `MONGODB_URI` and other credentials.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Run server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Integrations

To integrate this API into your existing websites, provide the `X-API-Key` configured in your `.env`.

**PHP Example (WordPress/WooCommerce)**
```php
$response = wp_remote_get('https://your-app.onrender.com/api/v1/fraud-check/01676225090', [
    'headers' => ['X-API-Key' => 'your-secret-api-key']
]);
$data = json_decode(wp_remote_retrieve_body($response), true);
```

## Dashboard Access
Navigate to `/` or `/login`. Use the `APP_PASSWORD` defined in `.env`.
