import asyncio
import httpx

async def test_order_with_valid_zone():
    url = 'https://developers.carrybee.com/api/v2/orders'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Client-ID': '7d219ad7-d1e3-4c54-b83a-f66913793d79',
        'Client-Secret': '0071546f-6aaf-4ccb-aba4-f6e198516758',
        'Client-Context': 'gvxHJdmfrXBVPaH7Dyuvtw6ESeTjU9'
    }
    payload = {
        'store_id': '652',
        'merchant_order_id': 'TEST-3005',
        'delivery_type': 1,
        'product_type': 1,
        'recipient_name': 'Test',
        'recipient_phone': '01676225090',
        'recipient_address': 'uttara dhaka',
        'city_id': 14,
        'zone_id': 150, # Uttara Sector 5
        'item_weight': 200,
        'item_quantity': 1,
        'collectable_amount': 69
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        print(f"Status: {resp.status_code}")
        print(f"Body: {resp.text}")

asyncio.run(test_order_with_valid_zone())
