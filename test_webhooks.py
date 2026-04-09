import asyncio
import httpx

async def test_webhook():
    test_carrybee_handshake = {
        "event": "webhook.integration"
    }
    
    async with httpx.AsyncClient() as client:
        # test carrybee
        resp = await client.post('http://127.0.0.1:8000/api/v1/webhooks/carrybee', json=test_carrybee_handshake)
        print("Carrybee integration response code:", resp.status_code)
        print("Carrybee header:", resp.headers.get("X-CB-Webhook-Integration-Header"))

        # test pathao
        resp = await client.post('http://127.0.0.1:8000/api/v1/webhooks/pathao', json={"event": "webhook_integration"})
        print("Pathao response code:", resp.status_code)
        print("Pathao header:", resp.headers.get("X-Pathao-Merchant-Webhook-Integration-Secret"))

asyncio.run(test_webhook())
