from playwright.async_api import async_playwright, Browser
import base64
from typing import Optional
import asyncio

async def take_full_page_screenshot(url: str) -> Optional[str]:
    """
    Takes a full-page screenshot of the given URL using Playwright.
    Returns base64 encoded PNG image or None if failed.
    """
    browser = None
    try:
        async with async_playwright() as p:
            # Launch browser with specific configurations
            browser = await p.chromium.launch(
                headless=True,
            )
            
            # Create a new page with high-res viewport (within PIL limits)
            page = await browser.new_page(
                viewport={'width': 2560, 'height': 1440},  # 2.5K resolution
                device_scale_factor=2,  # 2x for high quality screenshots
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

            # Navigate to the URL with networkidle strategy and longer timeout
            try:
                await page.goto(url, wait_until='networkidle', timeout=60000)  # Increased timeout for high-res assets
            except Exception as e:
                print(f"Initial navigation strategy failed: {str(e)}")
                # Fallback to domcontentloaded if networkidle times out
                await page.goto(url, wait_until='domcontentloaded')
                # Add a longer delay for high-res content
                await asyncio.sleep(4)

            # Handle lazy loading by scrolling
            await handle_lazy_loading(page)

            # Take the screenshot with maximum quality
            screenshot_bytes = await page.screenshot(
                full_page=True,
                type='png',
                scale='device',
                animations='disabled'  # Prevent animation frames from affecting quality
            )

            # Convert to base64
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            return base64_image

    except Exception as e:
        print(f"Error taking screenshot: {str(e)}")
        return None
    finally:
        if browser:
            try:
                await browser.close()
            except Exception as e:
                print(f"Error closing browser: {str(e)}")

async def handle_lazy_loading(page):
    """
    Handles lazy loading by scrolling through the page.
    Ensures all images and dynamic content are loaded before taking the screenshot.
    """
    try:
        # Get page height
        page_height = await page.evaluate('document.documentElement.scrollHeight')
        viewport_height = await page.evaluate('window.innerHeight')
        
        # Scroll in smaller steps for smoother loading
        step_size = viewport_height // 2  # Smaller steps
        for current_scroll in range(0, page_height, step_size):
            await page.evaluate(f'window.scrollTo(0, {current_scroll})')
            await asyncio.sleep(0.8)  # Longer wait for high-res content
            
        # Scroll back to top
        await page.evaluate('window.scrollTo(0, 0)')
        
        # Wait for network to be idle
        await page.wait_for_load_state('networkidle')
        
        # Wait for images to load with high-res check
        await page.evaluate('''
            Promise.all([
                // Wait for all images
                ...Array.from(document.images).map(img => {
                    if (img.complete) return Promise.resolve();
                    return new Promise((resolve) => {
                        img.onload = img.onerror = resolve;
                    });
                }),
                // Wait for background images
                ...Array.from(document.querySelectorAll('*')).map(el => {
                    const style = window.getComputedStyle(el);
                    if (style.backgroundImage && style.backgroundImage !== 'none') {
                        return new Promise(resolve => {
                            const img = new Image();
                            img.onload = img.onerror = resolve;
                            img.src = style.backgroundImage.replace(/url\\(['"](.+)['"]\\)/, '$1');
                        });
                    }
                    return Promise.resolve();
                }).filter(Boolean)
            ])
        ''')
        
        # Final wait to ensure everything is rendered
        await asyncio.sleep(1)
        
    except Exception as e:
        print(f"Error during lazy loading handling: {str(e)}")
        # Re-raise the exception to be handled by the caller
        raise 