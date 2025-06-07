import asyncio
from playwright.async_api import async_playwright

async def install_browsers():
    """Install the required browsers for Playwright"""
    async with async_playwright() as p:
        # Install Chromium
        print("Installing Chromium...")
        await p.chromium.install()
        print("Installation complete!")

if __name__ == "__main__":
    asyncio.run(install_browsers()) 