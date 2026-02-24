import asyncio
import aiohttp
import sys

async def main():
    print("Testing aiohttp...")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get('http://web.archive.org/', timeout=10) as resp:
                print(f"Status: {resp.status}")
                print("Success!")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
