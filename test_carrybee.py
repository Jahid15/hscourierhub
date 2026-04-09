import asyncio
from app.services.courier_entry.carrybee import CarrybeeEntry

async def test():
    creds = {
        'base_url': 'https://sandbox.carrybee.com',
        'client_id': '1a89c1a6-fc68-4395-9c09-628e0d3eaafc',
        'client_secret': '1d7152c9-5b2d-4e4e-9c20-652b93333704',
        'client_context': 'DzJwPsx31WaTbS745XZoBjmQLcNqwK'
    }
    c = CarrybeeEntry(creds)
    print(await c.parse_address('uttara dhaka'))

asyncio.run(test())
