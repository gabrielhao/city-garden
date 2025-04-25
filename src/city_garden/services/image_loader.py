from azure.storage.blob import BlobClient
from io import BytesIO
from PIL import Image
import re
import requests
from dotenv import load_dotenv
import os
import base64

class AzureImageLoader:
    def __init__(self, account_name: str, account_key: str):
        load_dotenv()
        self.account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
        self.account_key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]

    def _parse_blob_url(self, blob_url):
        # Extract container name and blob name from URL
        pattern = rf"https://{self.account_name}\.blob\.core\.windows\.net/([^/]+)/(.+)"
        match = re.match(pattern, blob_url)
        if not match:
            raise ValueError("Invalid blob URL or does not match account name.")
        container_name, blob_name = match.groups()
        return container_name, blob_name

    def load_image(self, blob_url):
        container_name, blob_name = self._parse_blob_url(blob_url)
        blob_client = BlobClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            container_name=container_name,
            blob_name=blob_name,
            credential=self.account_key
        )

        stream = BytesIO()
        blob_client.download_blob().readinto(stream)
        stream.seek(0)
        image = Image.open(stream)
        image_content = base64.b64encode(image).decode('utf-8')
        return image_content


    def load_images(self, blob_urls):
        image_contents = []
        for blob_url in blob_urls:
            image_contents.append(self.load_image(blob_url))
        return image_contents
    

# TEST CODE
# if __name__ == "__main__":
#     # Load environment variables
#     load_dotenv()
    
#     # Initialize the image loader
#     image_loader = AzureImageLoader(
#         account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
#         account_key=os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
#     )
    
#     # Test loading a single image
#     try:
#         # Replace with an actual blob URL from your Azure storage
#         test_blob_url = "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-compass.jpeg"
#         print(f"Loading image from: {test_blob_url}")
#         image = image_loader.load_image(test_blob_url)
#         print(f"Successfully loaded image: {image.size}")
        
#         # Display image information
#         print(f"Image size: {image.size}")
#         print(f"Image mode: {image.mode}")
#         print(f"Image format: {image.format}")
        
#         # Test loading multiple images
#         test_blob_urls = [
#             "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-1.jpeg",
#             "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-2.jpeg"
#         ]
#         print(f"\nLoading multiple images from: {test_blob_urls}")
#         images = image_loader.load_images(test_blob_urls)
#         print(f"Successfully loaded {len(images)} images")
        
#         for i, img in enumerate(images):
#             print(f"Image {i+1} size: {img.size}")
    
#     except Exception as e:
#         print(f"Error: {str(e)}")
    

