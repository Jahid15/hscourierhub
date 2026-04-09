import asyncio
import httpx
import json

async def get_zones():
    url = 'https://developers.carrybee.com/api/v2/cities/14/zones'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Client-ID': '7d219ad7-d1e3-4c54-b83a-f66913793d79',
        'Client-Secret': '0071546f-6aaf-4ccb-aba4-f6e198516758',
        'Client-Context': 'gvxHJdmfrXBVPaH7Dyuvtw6ESeTjU9'
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        data = resp.json()
        zones = data.get('data', {}).get('zones', [])
        print("TOTAL ZONES:", len(zones))
        for z in zones:
            if 'uttara' in z['name'].lower():
                print(f"{z['id']} - {z['name']}")
                
        # Also print what 1079 and 1082 are
        for z in zones:
            if z['id'] in [1079, 1082]:
                print(f"CHECK {z['id']} - {z['name']}")

asyncio.run(get_zones())
