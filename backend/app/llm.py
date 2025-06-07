import os
import base64
from openai import AsyncOpenAI, APIError, APITimeoutError, RateLimitError
from dotenv import load_dotenv
import io
from PIL import Image
from typing import List, Tuple, Optional

load_dotenv()

# Initialize OpenAI client with OpenRouter configuration
api_key = os.getenv("OPENROUTER_API_KEY")
if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable is not set")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key,
)

# Claude image constraints
MAX_DIMENSION = 7990  # Keeping slightly under 8000px to be safe
MAX_BASE64_SIZE_BYTES = 5 * 1024 * 1024  # 5MB in bytes
JPEG_QUALITY = 85  # Default JPEG quality
MIME_TYPE = "data:image/jpeg;base64,"  # Correct MIME type for JPEG images

SYSTEM_PROMPT = """You are an expert frontend web developer with perfect visual perception and attention to detail.

Your task is to recreate a complete web page based on a visual screenshot provided by the user.

Instructions:
- Generate a complete HTML file that visually replicates the screenshot as accurately as possible.
- Pay close attention to layout, font size, font family, colors, spacing, and image placement.
- Use modern, clean HTML and CSS. JavaScript is optional unless needed for UI behavior.
- You may use placeholder images like https://placehold.co/600x400 if the screenshot contains real images.
- Do not include markdown or backticks (no ```), just return the raw HTML starting with <html>.
- Do not leave out or summarize sections — fully code everything visible in the screenshot.
- If multiple elements are visually repeated, write out their full HTML copies.

Output only a full standalone HTML file."""

MULTI_IMAGE_SYSTEM_PROMPT = """You are an expert frontend web developer with perfect visual perception and attention to detail.

Your task is to recreate a complete web page based on multiple screenshot segments that represent different parts of the same webpage.

Instructions:
- The images provided are vertical slices of a single webpage, ordered from top to bottom.
- Generate a complete HTML file that visually replicates the entire webpage as accurately as possible.
- Ensure smooth transitions between the segments in your HTML recreation.
- Pay close attention to layout, font size, font family, colors, spacing, and image placement.
- Use modern, clean HTML and CSS. JavaScript is optional unless needed for UI behavior.
- You may use placeholder images like https://placehold.co/600x400 if the screenshot contains real images.
- Do not include markdown or backticks (no ```), just return the raw HTML starting with <html>.
- Do not leave out or summarize sections — fully code everything visible in all screenshot segments.
- If multiple elements are visually repeated, write out their full HTML copies.

Output only a full standalone HTML file that combines all segments into a cohesive webpage."""

class ImageValidationError(Exception):
    """Custom exception for image validation failures"""
    pass

def validate_and_optimize_slice(img_slice: Image.Image, slice_num: int = 0) -> str:
    """
    Validates and optimizes an image slice according to Claude's requirements.
    Returns base64 encoded string if valid, raises ImageValidationError if not.
    """
    # Check dimensions
    width, height = img_slice.size
    if width >= MAX_DIMENSION or height >= MAX_DIMENSION:
        raise ImageValidationError(f"Slice {slice_num} dimensions ({width}x{height}) exceed {MAX_DIMENSION}px limit")

    # Start with high quality and gradually reduce if needed
    quality = JPEG_QUALITY
    while quality >= 20:  # Don't go below quality 20
        buffer = io.BytesIO()
        img_slice.save(buffer, format='JPEG', quality=quality, optimize=True)
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        # Check size
        if len(base64_data) <= MAX_BASE64_SIZE_BYTES:
            print(f"Slice {slice_num}: {width}x{height}, Quality: {quality}, Size: {len(base64_data)/1024/1024:.2f}MB")
            return base64_data
            
        quality -= 5  # Reduce quality and try again
    
    raise ImageValidationError(f"Slice {slice_num} cannot be compressed to under 5MB even at lowest quality")

def slice_image(base64_string: str) -> List[str]:
    """
    Slice an image into segments if its height exceeds MAX_DIMENSION.
    Returns a list of base64-encoded image segments, each validated against Claude's requirements.
    """
    try:
        # Decode base64 to bytes
        image_data = base64.b64decode(base64_string)
        
        # Open with Pillow
        with Image.open(io.BytesIO(image_data)) as img:
            # Convert to RGB (removing alpha channel if present)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                img = img.convert('RGB')
            
            width, height = img.size
            print(f"Original image dimensions: {width}x{height}")
            
            # If image is within limits, validate and return as single slice
            if height <= MAX_DIMENSION:
                return [validate_and_optimize_slice(img)]
            
            # Calculate number of slices needed
            num_slices = (height + MAX_DIMENSION - 1) // MAX_DIMENSION
            slice_height = height // num_slices
            print(f"Slicing into {num_slices} segments of ~{slice_height}px height")
            
            # Create slices
            slices = []
            for i in range(num_slices):
                top = i * slice_height
                # For the last slice, use the remaining height
                bottom = min((i + 1) * slice_height, height)
                
                # Crop and validate each slice
                slice_img = img.crop((0, top, width, bottom))
                slice_base64 = validate_and_optimize_slice(slice_img, i + 1)
                slices.append(slice_base64)
            
            return slices
            
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise

async def analyze_screenshot(image_base64: str) -> Optional[str]:
    """
    Analyze a screenshot using OpenRouter's Claude Sonnet model and return HTML code.
    Returns None if the analysis fails.
    """
    try:
        # Slice the image if needed
        image_slices = slice_image(image_base64)
        print(f"Number of slices: {len(image_slices)}")
        
        if len(image_slices) == 1:
            # Single image case
            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this webpage screenshot and generate the HTML code to recreate it."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"{MIME_TYPE}{image_slices[0]}"
                            }
                        }
                    ]
                }
            ]
        else:
            # Multiple slices case
            content = [
                {
                    "type": "text",
                    "text": "Please analyze these webpage screenshot segments and generate the HTML code to recreate the complete page."
                }
            ]
            for i, slice_base64 in enumerate(image_slices):
                content.append({
                    "type": "text",
                    "text": f"Segment {i+1} of {len(image_slices)}:"
                })
                content.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"{MIME_TYPE}{slice_base64}"
                    }
                })
            
            messages = [
                {
                    "role": "system",
                    "content": MULTI_IMAGE_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": content
                }
            ]

        # Make API call with proper error handling
        try:
            print("Making API call to OpenRouter...")
            response = await client.chat.completions.create(
                model="anthropic/claude-sonnet-4",
                messages=messages,
                extra_headers={
                    "HTTP-Referer": os.getenv("HTTP_REFERER", "http://localhost:3000"),
                    "X-Title": "Orchids Challenge",
                }
            )
            print(f"API Response: {response}")
            
            if not response or not response.choices:
                print("Error: Empty response from API")
                print(f"Full response object: {response}")
                return None
                
            if not response.choices[0] or not response.choices[0].message:
                print("Error: No message in API response")
                print(f"Response choices: {response.choices}")
                return None
                
            content = response.choices[0].message.content
            if not content:
                print("Error: Empty content in API response")
                print(f"Message content: {response.choices[0].message}")
                return None
                
            return content
            
        except RateLimitError as e:
            print(f"Rate limit error: {str(e)}")
            print(f"Full error details: {e.__dict__}")
            raise
        except APITimeoutError as e:
            print(f"API timeout error: {str(e)}")
            print(f"Full error details: {e.__dict__}")
            raise
        except APIError as e:
            print(f"API Error: {str(e)}")
            print(f"Full error details: {e.__dict__}")
            raise
        except Exception as e:
            print(f"Unexpected error during API call: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {e.__dict__}")
            raise
        
    except ImageValidationError as e:
        print(f"Image validation error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error analyzing screenshot: {str(e)}")
        raise 