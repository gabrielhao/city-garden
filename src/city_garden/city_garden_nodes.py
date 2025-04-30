from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Dict, Any, List, TypedDict, Annotated, Optional
import sys
import os
import json
from datetime import datetime
from azure.storage.blob import BlobClient
import base64
from io import BytesIO

from city_garden.garden_state import GardenState
from city_garden.tools.climate import get_monthly_average_temperature, get_monthly_precipitation, get_wind_pattern
from city_garden.services.image_loader import AzureImageLoader
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from langchain_core.callbacks.manager import CallbackManager
import re
import logging
from city_garden.llm import llm
logger = logging.getLogger(__name__)
from io import BytesIO
from base64 import b64decode
from openai import OpenAI

load_dotenv()


""" 
City Garden Graph is a state graph that defines the flow of the city garden project. 
with time, images, it retrieves "sun_exposure", "micro_climate", "hardscape_elements", "plant_iventory".
with location, it retrieves "environment_factors" with tool calling openweathermap api.
with compass information, images, it retrieves "wind_pattern".
with user input, it gets "style_preferences" directly from user input.

The graph has 5 nodes that run in parallel:
Node 1: Get "sun_exposure", "micro_climate", "hardscape_elements", "plant_iventory"
Node 2: Get "environment_factors"
Node 3: Get "wind_pattern"
Node 4: Get "style_preferences"
Node 5: Generate final output. Take garden_info and plant_recommendations and create a final output. 

"""

# [+] add model
# [+] add images
# [+] add langsmith tracing
# [+] merge nodes
# [+] add tool binding
# [+] add location input
# [+] update prompt
# [+] debug all
# [+] move images to the state
# [+] add content safety
# [+] finalize the code
# [+] integrate with the website

def check_compliance(state: GardenState) -> GardenState:
    """
    Check compliance of the generated content.
    """
    print("Checking compliance")
    
    system_prompt = """
    You are a photo compliance inspector. Review the uploaded images and determine if they meet the following criteria:

    - The images primarily show a balcony, a small garden, or an indoor/outdoor space suitable for growing plants.

    Respond only with 'Pass' or 'Fail' — no additional explanation is needed.
    """

    garden_image_contents = state["images"]
    
    # Create message content with all images
    message_content = [{'type': 'text', 'text': f"Analyze the images."}]
    for image_content in garden_image_contents:
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_content}"
            }
        })
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message_content)
    ]  
    
    response = llm.invoke(messages)
    state["compliance_check"] = response.content
    
    print(f"Compliance check: {state['compliance_check']}")
    
    return state

def analyze_garden_conditions(state: GardenState) -> GardenState:
    """
    Analyze garden conditions based on garden images, compass information, location information.
    Sets sun_exposure, micro_climate, hardscape_elements, and plant_inventory, environment_factors, wind_pattern.
    Environment_factors and wind_pattern are retrieved from openweathermap api and weatherbit api.
    """
    print("Analyzing garden conditions")
    # Get garden information from LLM
    system_prompt = """
    You are a geography expert specializing in environmental analysis for horticulture.
    Based on several uploaded images taken from different angles, a photo of a compass, your task is to:
    
    - Identify the latitude, longitude and altitude information from the compass image for your analysis in the next step.
    - Extract and analyze the key geographical and environmental features relevant to growing plants.
 
    Return a JSON object with the following fields, and don't add any other keys:
    {
        "sun_exposure": "<Description of sun exposure patterns based on orientation and shadows>"
        "micro_climate": "<Note variations caused by buildings, trees, or structures that create unique temperature or moisture conditions within the site.>"
        "hardscape_elements": "<Presence and impact of non-plant structures like walls, pavements, fences, etc.>"
        "plant_inventory": "<Document existing plants, trees, and shrubs, including their health, size, and location. Decide which to retain, transplant, or remove.>"
        "environmental_factors": "<Map existing structures such as patios, paths, fences, sheds, utilities (overhead and underground), and any other built features.>"
        "wind_pattern": "<Prevailing wind directions, obstructions, and intensity patterns>"
    }
    
    Make sure your analysis is practical and tailored to optimizing plant growth at the specified location.
    """
    
    garden_image_contents = state["images"]
    
    print(f"Garden image contents loaded: {len(garden_image_contents)}")

    # Create message content with all images
    message_content = [{'type': 'text', 'text': f"Analyze the images. The latitude and longitude are {state['latitude']} and {state['longitude']}."}]
    for image_content in garden_image_contents:
        message_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{image_content}"
            }
        })
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=message_content)
    ] 
    
    response = llm.invoke(messages)
    
    print(f"Response: {response.content}")
    
    response_content = response.content
    
    # Parse the response (in a real implementation, this would be more robust)
    # For simplicity, we'll extract the information from the text
    if "sun_exposure" in response_content:
        state["sun_exposure"] = extract_value(response_content, "sun_exposure")
    else:
        state["sun_exposure"] = "None, no inpput information"
        
    if "micro_climate" in response_content:
        state["micro_climate"] = extract_value(response_content, "micro_climate")
    else:
        state["micro_climate"] = "None, no inpput information"
        
    if "hardscape_elements" in response_content:
        state["hardscape_elements"] = extract_value(response_content, "hardscape_elements")
    else:
        state["hardscape_elements"] = "None, no inpput information"
        
    if "plant_inventory" in response_content:
        state["plant_iventory"] = extract_value(response_content, "plant_inventory")
    else:
        state["plant_iventory"] = "None currently, new garden"
    
    if "environment_factors" in response_content:
        state["environment_factors"] = extract_value(response_content, "environment_factors")
    else:
        state["environment_factors"] = "None, no inpput information"
    
    if "wind_pattern" in response_content:
        state["wind_pattern"] = extract_value(response_content, "wind_pattern")
    else:
        state["wind_pattern"] = "None, no inpput information"
    
    # Add a message about the analysis
    state["messages"].append({
        "role": "assistant",
        "content": f"I've analyzed your garden conditions based on the provided information. {response_content}"
    })
    
    return state


def generate_final_output(state: GardenState) -> GardenState:
    """
    Generate final output. Take garden_info and plant_recommendations and create a final output. 
    Final output should be a structured report with the following sections:
    - Introduction
    - Garden Analysis
    - Plant Recommendations
    - Design Recommendations
    - Conclusion
    """
    print("Generating final output")
    # Get garden information from state
    garden_info = f"""
    Sun exposure: {state.get('sun_exposure', 'Not analyzed')}
    Micro climate: {state.get('micro_climate', 'Not analyzed')}
    Hardscape elements: {state.get('hardscape_elements', 'Not analyzed')}
    Plant inventory: {state.get('plant_iventory', 'Not analyzed')}
    Environment factors: {state.get('environment_factors', 'Not analyzed')}
    Wind pattern: {state.get('wind_pattern', 'Not analyzed')}
    """
    
    # User's preferences
    preferences = state.get('style_preferences', 'Not analyzed')
    
    # Create a prompt for the LLM to generate a structured report
    system_prompt = """
    You are a botany expert. Your task is to recommend suitable plants for someone who wants to create a small garden on their balcony. Please consider the following environmental conditions and preferences:

    ### User's preferences:
    {preferences}

    ### Environment information:
    {garden_info}

    Based on this context, please generate a list of at least 3 suitable plants that would thrive in these conditions following the JSON structure below:
    {
      "plant_recommendations": [
        {
          "id": 0,
          "name": "<plantA>",
          "description": "<A description of plantA.>",
          "care_tips": "<Care tips of plantA.>"
        },
        {
          "id": 1,
          "name": "<plantB>",
          "description": "<A description of plantB.>",
          "care_tips": "<Care tips of plantB.>"
        },
        {
          "id": 2,
          "name": "<plantC>",
          "description": "<A description of plantC.>",
          "care_tips": "<Care tips of plantC.>"
        },
        ...
      ]
    }
    The JSON should start with key "plant_recommendations" and end with key "}"
    """
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"""
        Create a comprehensive garden design report based on the following information:
        
        GARDEN INFORMATION:
        {garden_info}
        
        USER PREFERENCES:
        {preferences}
        
        Please structure the report with the sections mentioned in the system prompt.
        """)
    ]
    
    # Generate the final report
    response = llm.invoke(messages)
    final_report = response.content
    
    #print(f"Final report: {final_report}")
    
    if "plant_recommendations" in final_report:
        state["plant_recommendations"] = json.loads(final_report)["plant_recommendations"]
        print(f"Plant Recommendations: {state['plant_recommendations']}")
    else:
        state["plant_recommendations"] = "None, no information"
    
    # Store the final report in the state
    state["final_output"] = final_report
    
    # Add the final report to the messages
    state["messages"].append({
        "role": "assistant",
        "content": "I've generated a comprehensive garden design report for you."
    })
    
    state["messages"].append({
        "role": "assistant",
        "content": final_report
    })
    
    return state


def create_garden_image(state: GardenState) -> GardenState:
    """
    Create a garden image based on the garden information and plant recommendations. The image should be in colorful hand-drawn style.
    The image is created by LLM. For debugging, the image is shown.
    """
    
    load_dotenv()

    def generate_image_with_gpt(balcony_description: str, image_files: List[BytesIO]) -> Optional[str]:
        client = OpenAI()
        try:
            response = client.images.edit(
                model="gpt-image-1",
                image=image_files,
                prompt=balcony_description
            )
            
            # with open("balcony.png", "wb") as file:
            #     file.write(b64decode(response.data[0].b64_json))
            
            # print("Balcony image saved.")
            
            image_loader = AzureImageLoader(
                account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
                account_key=os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
            )
            
            image_content = response.data[0].b64_json
            blob_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}-garden_image.png"
            
            image_url = image_loader.upload_image(b64decode(image_content), "images", blob_name)
            state["garden_image_url"] = image_url
            
            print(f"Garden image URL: {state['garden_image_url']}")
            
            return image_content
        
        except Exception as err:
            print("Error generating image:", err)
            return None
    
    
    # Get garden information from state
    garden_image_contents = state.get('images', 'Not analyzed')
    plant_recommendations = state.get('plant_recommendations', 'Not analyzed')
    
    # Wrap loaded Azure images as file-like objects
    print("Wrapping loaded Azure images as file-like objects")
    image_files = []
    for idx, img_bytes in enumerate(garden_image_contents):
        bio = BytesIO(base64.b64decode(img_bytes))
        bio.name = f"image_{idx}.jpeg"  # <-- Give it a filename with proper extension!
        image_files.append(bio)

    system_prompt = f"""
    You are a professional image editor. Given multiple uploaded images taken from different angles of a balcony and a list of plants, your task is to:

    - Generate an image that shows the visual effect of growing some or all of the listed plants within the provided scenes.
    - Do not modify any other parts of the original images.
    - Keep the image in colorful sketch style.
    
    ### Plants to be grown:
    {plant_recommendations}
    """

    print("Generating image with GPT")
    try:
        response = generate_image_with_gpt(balcony_description=system_prompt, image_files=image_files)
        if response is None:
            print("Error: Failed to generate image with GPT")
            return state
            
        print("Image generated successfully with GPT")
        state["garden_image"] = response
            
    except Exception as e:
        print(f"Error during GPT image generation: {str(e)}")
        return state
            
    return state

def extract_value(text: str, key: str) -> Optional[str]:
    """Extract a value from text using JSON parsing.
    
    Args:
        text: The text to search in (should be JSON)
        key: The key to look for
        
    Returns:
        The extracted value or None if not found
        
    Raises:
        ValueError: If the text is empty or invalid
    """

    if not text or not isinstance(text, str):
        raise ValueError("Text must be a non-empty string")
        
    try:
        # Try to parse the text as JSON
        import json
        # Remove markdown code block if present
        text = text.strip('`').strip()
        if text.startswith('json'):
            text = text[4:].strip()
        data = json.loads(text)
        
        # Get the value for the key
        value = data.get(key)
        if value is None:
            logger.warning(f"No value found for key '{key}' in JSON")
            return None
            
        # Convert lists to strings
        if isinstance(value, list):
            return ', '.join(str(item) for item in value)
            
        return str(value)
    except json.JSONDecodeError:
        # If not valid JSON, try regex as fallback
        try:
            pattern = rf"{key}:\s*([^\n]+)"
            match = re.search(pattern, text)
            if not match:
                logger.warning(f"No match found for key '{key}' in text")
                return None
            return match.group(1).strip()
        except Exception as e:
            logger.error(f"Error extracting value for key '{key}': {str(e)}")
            return None
    except Exception as e:
        logger.error(f"Error extracting value for key '{key}': {str(e)}")
        return None

def upload_image(image_content: str, container_name: str, blob_name: str) -> str:
    """Upload an image to Azure Blob Storage and return its URL."""
    blob_client = BlobClient(
        account_url=f"https://{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}.blob.core.windows.net",
        container_name=container_name,
        blob_name=blob_name,
        credential=os.environ['AZURE_STORAGE_ACCOUNT_KEY']
    )
    
    # Convert base64 to bytes and upload
    image_bytes = base64.b64decode(image_content)
    blob_client.upload_blob(image_bytes, overwrite=True)
    
    # Generate and return the URL
    return f"https://{os.environ['AZURE_STORAGE_ACCOUNT_NAME']}.blob.core.windows.net/{container_name}/{blob_name}"


