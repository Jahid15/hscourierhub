import asyncio
import httpx

async def test_interceptor():
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Client-ID': '7d219ad7-d1e3-4c54-b83a-f66913793d79',
        'Client-Secret': '0071546f-6aaf-4ccb-aba4-f6e198516758',
        'Client-Context': 'gvxHJdmfrXBVPaH7Dyuvtw6ESeTjU9'
    }
    
    query = "uttara dhaka bangladesh"
    
    url = f"https://developers.carrybee.com/api/v2/address-details"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json={"query": query}, headers=headers)
        data = resp.json()
        city_id = data['data']['city_id']
        zone_id = data['data']['zone_id']
        
        print(f"Parser returned City: {city_id}, Zone: {zone_id}")
        
    url_zones = f"https://developers.carrybee.com/api/v2/cities/{city_id}/zones"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url_zones, headers=headers)
        active_zones = resp.json()['data']['zones']
        
    is_valid = any(z['id'] == zone_id for z in active_zones)
    print(f"Is {zone_id} physically valid in active zones? {is_valid}")
    
    if not is_valid:
        query_words = [w for w in query.replace(',', ' ').lower().split() if len(w) > 3]
        for w in query_words:
            print(f"Checking fallback for word: {w}")
            match = next((z for z in active_zones if w in z['name'].lower()), None)
            if match:
                zone_id = match['id']
                print(f"FALLBACK SUCCESS: Mapped to {match['id']} - {match['name']}")
                break

asyncio.run(test_interceptor())
