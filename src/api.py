from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
from typing import List, Optional, Dict, Any
from city_garden.graph_builder import build_garden_graph
from city_garden.garden_state import GardenState
from city_garden.services.image_loader import AzureImageLoader
from city_garden.services.content_safety import ContentAnalyzer
import os
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="City Garden API", description="API for generating garden plans")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

class Location(BaseModel):
    latitude: float
    longitude: float
    address: str

class UserPreferences(BaseModel):
    growType: str
    subType: str
    cycleType: str
    winterType: str

class GardenPlanRequest(BaseModel):
    image_urls: List[str]  # Changed from HttpUrl to str to handle Azure SAS URLs
    user_preferences: UserPreferences
    location: Location

    @validator('image_urls')
    def validate_image_urls(cls, v):
        if not v:
            raise ValueError("At least one image URL is required")
        if len(v) > 3:
            raise ValueError("Maximum 3 images allowed")
        return v

class GardenPlanResponse(BaseModel):
    garden_image_url: str
    plant_recommendations: List[Dict[Any, Any]]

@app.post("/api/garden_plan", response_model=GardenPlanResponse)
async def create_garden_plan(request: GardenPlanRequest):
    try:
        logger.info(f"Received request with {len(request.image_urls)} images")
        
        # Load images
        image_loader = AzureImageLoader(
            account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
            account_key=os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
        )
        
        try:
            logger.info("Attempting to load images from Azure Blob Storage")
            garden_image_contents = image_loader.load_images(request.image_urls)
            logger.info(f"Successfully loaded {len(garden_image_contents)} images")
        except Exception as e:
            logger.error(f"Failed to load images: {str(e)}")
            raise HTTPException(status_code=400, detail=f"Failed to load images: {str(e)}")
        
        if len(garden_image_contents) == 0:
            logger.error("No images loaded successfully")
            raise HTTPException(status_code=400, detail="No images loaded successfully")
        
        # Check content safety
        content_analyzer = ContentAnalyzer(
            endpoint=os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"],
            key=os.environ["AZURE_CONTENT_SAFETY_KEY"]
        )
        
        for image_content in garden_image_contents:
            try:
                analysis_result = content_analyzer.analyze_image_data(image_content)
                if (analysis_result.hate_severity > 0.5 or 
                    analysis_result.self_harm_severity > 0.5 or 
                    analysis_result.sexual_severity > 0.5 or 
                    analysis_result.violence_severity > 0.5):
                    logger.error("Image content safety check failed")
                    raise HTTPException(status_code=400, detail="Image content safety check failed")
            except Exception as e:
                logger.error(f"Content safety analysis failed: {str(e)}")
                raise HTTPException(status_code=400, detail=f"Content safety analysis failed: {str(e)}")
        
        # Create the graph
        graph = build_garden_graph()
        
        # Format user preferences for the garden state
        style_preferences = f"{request.user_preferences.growType} {request.user_preferences.subType} plants, {request.user_preferences.cycleType}, {request.user_preferences.winterType}"
        
        # Initialize the state
        initial_state = GardenState(
            sun_exposure="",
            micro_climate="",
            hardscape_elements="",
            plant_iventory="",
            environment_factors="",
            wind_pattern="",
            style_preferences=style_preferences,
            plant_recommendations=[],
            garden_image_url="",
            garden_image="",
            location=request.location.address,
            latitude=request.location.latitude,
            longitude=request.location.longitude,
            images=garden_image_contents,
            messages=[]
        )
        
        # Run the graph
        logger.info("Running the garden planning graph")
        final_state = graph.invoke(initial_state)
        logger.info("Graph execution completed")
        
        # print out plant recommendations
        print(f"Plant recommendations: {final_state['plant_recommendations']}")
        print(f"Garden image URL: {final_state['garden_image_url']}")   
        
        # Return the results
        return GardenPlanResponse(
            garden_image_url=final_state['garden_image_url'],
            plant_recommendations=final_state['plant_recommendations']
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}") 