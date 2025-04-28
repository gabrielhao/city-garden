import os
import requests
from PIL import Image
from io import BytesIO

# Generate an image with DALL-E, return the image as Image object
def generate_image(prompt: str) -> Image.Image:
     # create image with DALL-E
    api_key = os.getenv("AZURE_DALLE_API_KEY")
    url = "https://jikiw-ma1bdakf-swedencentral.openai.azure.com/openai/deployments/dall-e-3/images/generations?api-version=2024-02-01"

    # Headers
    headers = {
        "Content-Type": "application/json",
        "api-key": api_key
    }

    # Request body (payload)
    data = {
        "model": "dall-e-3",
        "prompt": prompt,
        "size": "1024x1024",
        "style": "vivid",
        "quality": "standard",
        "n": 1
    }

    # Send POST request
    response = requests.post(url, headers=headers, json=data)

    # Check response
    if response.status_code == 200:
        print("Success!")
        print(response.json())
    else:
        print(f"Request failed with status code {response.status_code}: {response.text}")
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
    
    # Get the image URL from the response
    image_url = response.json()["data"][0]["url"]
    
    # Download the image
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    
    return image
    
    