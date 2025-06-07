from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Dict, List, Optional
from app.screenshot import take_full_page_screenshot
from app.llm import analyze_screenshot

# Create FastAPI instance
app = FastAPI(
    title="Orchids Challenge API",
    description="A starter FastAPI template for the Orchids Challenge backend",
    version="1.0.0"
)

# Add CORS middleware - More permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ScreenshotRequest(BaseModel):
    url: HttpUrl

class ScreenshotResponse(BaseModel):
    success: bool
    message: str
    image_data: Optional[str] = None
    generated_html: Optional[str] = None

class Item(BaseModel):
    id: int
    name: str
    description: str = None

class ItemCreate(BaseModel):
    name: str
    description: str = None

# In-memory storage for demo purposes
items_db: List[Item] = [
    Item(id=1, name="Sample Item", description="This is a sample item"),
    Item(id=2, name="Another Item", description="This is another sample item")
]

# Screenshot endpoint
@app.post("/screenshot", response_model=ScreenshotResponse)
async def take_screenshot(request: ScreenshotRequest):
    try:
        # Take screenshot
        image_data = await take_full_page_screenshot(str(request.url))
        if not image_data:
            raise HTTPException(
                status_code=500, 
                detail="Failed to capture screenshot. The URL might be invalid or the page might be blocking automated access."
            )
            
        # Analyze with LLM
        try:
            generated_html = await analyze_screenshot(image_data)
        except Exception as e:
            print(f"LLM analysis failed: {str(e)}")
            # Return a more informative error message
            return ScreenshotResponse(
                success=True,
                message="Screenshot captured but HTML generation failed",
                image_data=image_data,
                generated_html=None
            )
        
        return ScreenshotResponse(
            success=True,
            message="Screenshot captured and HTML generated successfully",
            image_data=image_data,
            generated_html=generated_html
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An unexpected error occurred: {str(e)}"
        )

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hello from FastAPI backend!", "status": "running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchids-challenge-api"}

# Get all items
@app.get("/items", response_model=List[Item])
async def get_items():
    return items_db

# Get item by ID
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    for item in items_db:
        if item.id == item_id:
            return item
    return {"error": "Item not found"}

# Create new item
@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    new_id = max([item.id for item in items_db], default=0) + 1
    new_item = Item(id=new_id, **item.dict())
    items_db.append(new_item)
    return new_item

# Update item
@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate):
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            updated_item = Item(id=item_id, **item.dict())
            items_db[i] = updated_item
            return updated_item
    return {"error": "Item not found"}

# Delete item
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    for i, item in enumerate(items_db):
        if item.id == item_id:
            deleted_item = items_db.pop(i)
            return {"message": f"Item {item_id} deleted successfully", "deleted_item": deleted_item}
    return {"error": "Item not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
