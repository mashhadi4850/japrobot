import aiohttp
import asyncio

NOWPAYMENTS_API_KEY = "GG4JR5Z-65J4W65-M5MACDZ-BGXSW8D"


async def check_payment_status(payment_id):
    url = f"https://api.nowpayments.io/v1/payment/{payment_id}"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(
                f"[DEBUG] Sending request to URL: {url} with headers: {headers}")
            response_json = await response.json()
            print(f"[DEBUG] Payment status response: {response_json}")
            return response_json


async def main_test():
    # جای payment_id رو با Payment ID واقعی پر کن
    payment_id = 4736074704
    status = await check_payment_status(payment_id)
    print(status)

if __name__ == "__main__":
    asyncio.run(main_test())
