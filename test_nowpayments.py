# test_nowpayments.py
import aiohttp
import asyncio

# API key جدید رو اینجا وارد کن
NOWPAYMENTS_API_KEY = "GG4JR5Z-65J4W65-M5MACDZ-BGXSW8D"


async def test_api_key():
    url = "https://api.nowpayments.io/v1/currencies"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            data = await response.json()
            print(f"Response: {data}")

asyncio.run(test_api_key())
