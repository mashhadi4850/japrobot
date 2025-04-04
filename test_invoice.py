import aiohttp
import asyncio

NOWPAYMENTS_API_KEY = "GG4JR5Z-65J4W65-M5MACDZ-BGXSW8D"

async def check_invoice_status(invoice_id):
    url = f"https://api.nowpayments.io/v1/invoice/{invoice_id}"
    headers = {"x-api-key": NOWPAYMENTS_API_KEY}
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            print(f"[DEBUG] Sending request to URL: {url} with headers: {headers}")
            response_json = await response.json()
            print(f"[DEBUG] Invoice status response: {response_json}")
            return response_json

async def main_test():
    status = await check_invoice_status("6432325028")
    print(status)

if __name__ == "__main__":
    asyncio.run(main_test())