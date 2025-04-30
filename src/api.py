from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
from city_garden.graph_builder import build_garden_graph
from city_garden.garden_state import GardenState
from city_garden.services.image_loader import AzureImageLoader
from city_garden.services.content_safety import ContentAnalyzer
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="City Garden API", description="API for generating garden plans")

class GardenPlanRequest(BaseModel):
    image_urls: List[HttpUrl]
    user_preferences: str
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class GardenPlanResponse(BaseModel):
    garden_image_url: str
    plant_recommendations: List[str]

@app.post("/api/garden_plan", response_model=GardenPlanResponse)
async def create_garden_plan(request: GardenPlanRequest):
    # Validate number of images
    if len(request.image_urls) > 3:
        raise HTTPException(status_code=400, detail="Maximum 3 images allowed")
    
    # Load images
    image_loader = AzureImageLoader(
        account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
        account_key=os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
    )
    
    try:
        garden_image_contents = image_loader.load_images([str(url) for url in request.image_urls])
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load images: {str(e)}")
    
    if len(garden_image_contents) == 0:
        raise HTTPException(status_code=400, detail="No images loaded successfully")
    
    # Check content safety
    content_analyzer = ContentAnalyzer(
        endpoint=os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"],
        key=os.environ["AZURE_CONTENT_SAFETY_KEY"]
    )
    
    for image_content in garden_image_contents:
        analysis_result = content_analyzer.analyze_image_data(image_content)
        if (analysis_result.hate_severity > 0.5 or 
            analysis_result.self_harm_severity > 0.5 or 
            analysis_result.sexual_severity > 0.5 or 
            analysis_result.violence_severity > 0.5):
            raise HTTPException(status_code=400, detail="Image content safety check failed")
    
    # Create the graph
    graph = build_garden_graph()
    
    # Initialize the state
    initial_state = GardenState(
        sun_exposure="",
        micro_climate="",
        hardscape_elements="",
        plant_iventory="",
        environment_factors="",
        wind_pattern="",
        style_preferences=request.user_preferences,
        plant_recommendations=[],
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        images=garden_image_contents,
        messages=[]
    )
    
    # Run the graph
    print("Running the graph")
    final_state = graph.invoke(initial_state)
    
    # Return the results
    return GardenPlanResponse(
        garden_image_url=final_state.get("garden_image_url", ""),
        plant_recommendations=final_state.get("plant_recommendations", [])
    ) 