# Orchids Challenge Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Setup Instructions](#setup-instructions)
   - [Prerequisites](#prerequisites)
   - [Backend Setup](#backend-setup)
   - [Frontend Setup](#frontend-setup)
3. [Environment Variables](#environment-variables)
4. [Project Structure](#project-structure)
5. [Backend Architecture](#backend-architecture)
   - [Main Application](#main-application-mainpy)
   - [Screenshot Module](#screenshot-module-screenshotpy)
   - [LLM Module](#llm-module-llmpy)
6. [API Documentation](#api-documentation)
   - [Screenshot Endpoints](#screenshot-endpoints)
   - [Item Management Endpoints](#item-management-endpoints)
   - [System Endpoints](#system-endpoints)
7. [Technical Details](#technical-details)
   - [Screenshot Processing Pipeline](#screenshot-processing-pipeline)
   - [Image Processing Constraints](#image-processing-constraints)
8. [Technical Challenges and Design Decisions](#technical-challenges-and-design-decisions)

## Project Overview
The Orchids Challenge project is a full-stack web application built using FastAPI for the backend and Next.js for the frontend. The project implements advanced webpage screenshot capture, AI-powered HTML generation, and web interactions. It uses Playwright for high-quality screenshots and OpenRouter's Claude model for intelligent HTML generation.

## Setup Instructions

### Prerequisites
- Python 3.x
- Node.js and npm
- uv package manager
- Playwright browser automation framework

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies using uv:
   ```bash
   uv sync
   ```

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

4. Start the FastAPI development server:
   ```bash
   uv run fastapi dev
   ```
## Environment Variables

Create a `.env` file based on `env.example` with the following variables:

```env
# Backend Environment Variables
OPENROUTER_API_KEY=your_openrouter_api_key    # Required for AI HTML generation
```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```


## Project Structure

```
orchids-challenge/
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── screenshot.py   # Playwright-based screenshot functionality
│   │   └── llm.py         # OpenRouter/Claude integration
│   ├── pyproject.toml     # Python project configuration
│   └── uv.lock           # Python dependencies lock file
│
├── frontend/
│   ├── src/
│   │   └── app/          # Next.js application code
│   ├── package.json      # Node.js dependencies and scripts
│   └── next.config.ts    # Next.js configuration
```

## Backend Architecture

### Main Application (main.py)
The main FastAPI application handles:
- API route definitions with Pydantic models for request/response validation
- CORS configuration for local development
- Screenshot capture and analysis pipeline
- RESTful CRUD operations for items
- Health check endpoints

Key Features:
- Type-safe request/response handling with Pydantic
- Error handling with proper HTTP status codes
- In-memory storage for demo purposes

### Screenshot Module (screenshot.py)
Advanced screenshot capture functionality:
- Uses Playwright for high-fidelity webpage rendering
- Supports high-resolution captures (2.5K resolution with 2x scaling)
- Handles lazy-loaded content through smart scrolling
- Implements browser-like headers and user agent
- Optimizes image quality and size
- Handles various page loading scenarios with fallbacks

Key Features:
- Full-page screenshot capability
- Lazy loading detection and handling
- High-DPI support
- Network idle detection
- Image optimization

### LLM Module (llm.py)
Manages AI-powered HTML generation:
- Integrates with OpenRouter's Claude model
- Handles large screenshots through intelligent slicing
- Implements image validation and optimization
- Provides detailed system prompts for accurate HTML generation

Key Features:
- Image size and dimension validation
- Automatic image slicing for large screenshots
- Quality-preserving compression
- Intelligent HTML generation with context awareness
- Support for multi-segment page analysis


## API Documentation

### Screenshot Endpoints
- `POST /api/screenshot`
  - Captures webpage screenshots and generates HTML
  - Parameters:
    ```json
    {
      "url": "https://example.com"  // Valid HTTP(S) URL
    }
    ```
  - Returns:
    ```json
    {
      "success": true,
      "message": "Screenshot captured and HTML generated successfully",
      "image_data": "base64_encoded_image",
      "generated_html": "generated_html_code"
    }
    ```

### Item Management Endpoints
- `GET /items`: List all items
- `GET /items/{item_id}`: Get item by ID
- `POST /items`: Create new item
- `PUT /items/{item_id}`: Update item
- `DELETE /items/{item_id}`: Delete item

### System Endpoints
- `GET /`: Root endpoint with service info
- `GET /health`: Health check endpoint

## Technical Details

### Screenshot Processing Pipeline
1. URL Validation and Request Processing
2. High-Resolution Screenshot Capture
   - 2560x1440 viewport
   - 2x device scale factor
   - Custom user agent and headers
3. Lazy Loading Handling
   - Progressive scrolling
   - Network idle detection
   - Image load verification
4. Image Optimization
   - JPEG compression
   - Size validation
   - Quality adjustment
5. AI Processing
   - Image slicing if needed
   - Claude model integration
   - HTML generation

### Image Processing Constraints
- Maximum dimension: 7990px
- Maximum base64 size: 5MB
- Default JPEG quality: 85
- Automatic quality adjustment
- RGB color space conversion

## Technical Challenges and Design Decisions

### 1. High-Quality Screenshot Capture

#### Challenges:
1. **Lazy Loading Content**
   - Modern websites often use lazy loading for images and content
   - Simple screenshot tools would miss dynamically loaded content
   - Some content only loads when scrolled into view

#### Solution:
- Implemented sophisticated scrolling logic in `screenshot.py`:
  ```python
  async def handle_lazy_loading(page):
      # Smart progressive scrolling
      step_size = viewport_height // 2
      for current_scroll in range(0, page_height, step_size):
          await page.evaluate(f'window.scrollTo(0, {current_scroll})')
          await asyncio.sleep(0.8)  # Longer wait for high-res content
  ```
- Added intelligent waiting mechanisms for:
  - Network requests to complete
  - Images to fully load
  - Background images to render
  - Dynamic content to appear

### 2. Image Quality vs Size Constraints

#### Challenges:
1. **Claude Model Limitations**
   - Maximum image dimension: 8000px
   - Maximum base64 size: 5MB
   - Need for high-quality screenshots

#### Solution:
- Implemented adaptive image processing in `llm.py`:
  - Start with high quality (85)
  - Progressively reduce quality if size limit exceeded
  - Automatic image slicing for tall pages
  ```python
  def validate_and_optimize_slice(img_slice: Image.Image, slice_num: int = 0):
      quality = JPEG_QUALITY
      while quality >= 20:
          # Progressive quality reduction while maintaining visibility
          buffer = io.BytesIO()
          img_slice.save(buffer, format='JPEG', quality=quality, optimize=True)
          # ... size checking and optimization logic
  ```

### 3. Browser Automation Reliability

#### Challenges:
1. **Website Compatibility**
   - Anti-bot measures
   - Dynamic loading patterns
   - Various viewport sizes

#### Solution:
- Implemented robust browser configuration:
  ```python
  browser = await p.chromium.launch(headless=True)
  page = await browser.new_page(
      viewport={'width': 2560, 'height': 1440},
      device_scale_factor=2,
      user_agent='Mozilla/5.0 ...'
  )
  ```
- Added fallback navigation strategies:
  ```python
  try:
      await page.goto(url, wait_until='networkidle', timeout=60000)
  except Exception:
      # Fallback to simpler strategy
      await page.goto(url, wait_until='domcontentloaded')
      await asyncio.sleep(4)
  ```

### 4. AI HTML Generation

#### Challenges:
1. **Accurate Visual Recreation**
   - Maintaining visual fidelity
   - Handling complex layouts
   - Preserving styling details

#### Solution:
- Crafted detailed system prompts:
  ```python
  SYSTEM_PROMPT = """You are an expert frontend web developer with perfect visual perception...
  - Generate a complete HTML file that visually replicates the screenshot
  - Pay close attention to layout, font size, font family, colors, spacing
  - Use modern, clean HTML and CSS
  """
  ```
- Implemented multi-segment analysis for large pages:
  - Split pages into manageable segments
  - Maintain context between segments
  - Ensure smooth visual transitions

### 5. API Design and Error Handling

#### Challenges:
1. **Robust Error Management**
   - Multiple failure points
   - Long-running operations
   - Resource cleanup

#### Solution:
- Implemented comprehensive error handling:
  ```python
  try:
      image_data = await take_full_page_screenshot(str(request.url))
      if not image_data:
          raise HTTPException(status_code=500, 
              detail="Failed to capture screenshot...")
  except Exception as e:
      raise HTTPException(status_code=500, 
          detail=f"An unexpected error occurred: {str(e)}")
  ```
- Added proper resource cleanup:
  ```python
  finally:
      if browser:
          try:
              await browser.close()
          except Exception as e:
              print(f"Error closing browser: {str(e)}")
  ```

### 6. Performance Optimization

#### Challenges:
1. **Resource Management**
   - Memory usage during image processing
   - Browser instance management
   - API response times

#### Solution:
- Implemented efficient image processing:
  - Progressive JPEG compression
  - Memory-efficient image handling
  - Proper resource cleanup
- Browser optimization:
  - Single browser instance per request
  - Proper cleanup after use
  - Configurable timeouts

### 7. Security Considerations

#### Challenges:
1. **Safe URL Processing**
   - Potential malicious URLs
   - Resource exhaustion
   - Data privacy

#### Solution:
- Input validation using Pydantic:
  ```python
  class ScreenshotRequest(BaseModel):
      url: HttpUrl  # Validates URL format
  ```
- Secure browser configuration:
  - Headless mode
  - Resource limitations
  - Proper error handling

### 8. Development Workflow

#### Challenges:
1. **Local Development**
   - Environment consistency
   - Dependency management
   - Cross-platform compatibility

#### Solution:
- Structured project layout:
  - Clear separation of concerns
  - Modular architecture
  - Comprehensive documentation
- Development tools:
  - uv for Python dependency management
  - npm for frontend dependencies
  - Type checking and validation

These challenges and solutions shaped the project's architecture and implementation decisions, resulting in a robust and maintainable system that effectively handles webpage screenshot capture and HTML generation. 
