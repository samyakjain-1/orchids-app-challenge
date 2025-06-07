from playwright.async_api import async_playwright
import base64
from typing import Optional
import asyncio

async def take_full_page_screenshot(url: str) -> Optional[str]:
    """
    Takes a full-page screenshot of the given URL using Playwright.
    Returns base64 encoded PNG image or None if failed.
    """
    try:
        async with async_playwright() as p:
            # Launch browser with specific configurations
            browser = await p.chromium.launch(
                headless=True,
            )
            
            # Create a new page with desktop viewport
            page = await browser.new_page(
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            )
            
            # Set extra HTTP headers to appear more browser-like
            await page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            })

            # Navigate to the URL with networkidle strategy
            try:
                await page.goto(url, wait_until='networkidle', timeout=30000)
            except Exception:
                # Fallback to domcontentloaded if networkidle times out
                await page.goto(url, wait_until='domcontentloaded')
                # Add a small delay for additional content
                await asyncio.sleep(2)

            # Handle lazy loading by scrolling
            await handle_lazy_loading(page)

            # Take the screenshot
            screenshot_bytes = await page.screenshot(
                full_page=True,
                type='png'
            )

            # Convert to base64
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            await browser.close()
            return base64_image

    except Exception as e:
        print(f"Error taking screenshot: {str(e)}")
        return None

async def handle_lazy_loading(page):
    """
    Handles lazy loading by scrolling through the page.
    """
    try:
        # Get page height
        page_height = await page.evaluate('document.documentElement.scrollHeight')
        viewport_height = await page.evaluate('window.innerHeight')
        
        # Scroll in steps
        for current_scroll in range(0, page_height, viewport_height):
            await page.evaluate(f'window.scrollTo(0, {current_scroll})')
            await asyncio.sleep(0.5)  # Wait for content to load
            
        # Scroll back to top
        await page.evaluate('window.scrollTo(0, 0)')
        
        # Wait for images to load
        await page.wait_for_load_state('load')
        
        # Additional wait for any lazy-loaded images
        await page.evaluate('''
            Promise.all(
                Array.from(document.images)
                    .filter(img => !img.complete)
                    .map(img => new Promise(resolve => {
                        img.onload = img.onerror = resolve;
                    }))
            )
        ''')
        
    except Exception as e:
        print(f"Error during lazy loading handling: {str(e)}") 