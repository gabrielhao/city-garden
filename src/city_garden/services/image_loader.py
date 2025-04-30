from azure.storage.blob import BlobClient
from io import BytesIO
from PIL import Image
import re
import requests
from dotenv import load_dotenv
import os
import base64
from urllib.parse import urlparse, parse_qs

class AzureImageLoader:
    def __init__(self, account_name: str, account_key: str):
        load_dotenv()
        self.account_name = os.environ["AZURE_STORAGE_ACCOUNT_NAME"]
        self.account_key = os.environ["AZURE_STORAGE_ACCOUNT_KEY"]

    def _parse_blob_url(self, blob_url):
        # Parse the URL to handle SAS tokens
        parsed_url = urlparse(blob_url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if len(path_parts) < 2:
            raise ValueError("Invalid blob URL format")
            
        container_name = path_parts[0]
        blob_name = '/'.join(path_parts[1:])
        
        # If there's a SAS token, use it directly
        if parsed_url.query:
            return container_name, blob_name, parsed_url.query
        else:
            return container_name, blob_name, None

    def load_image(self, blob_url):
        container_name, blob_name, sas_token = self._parse_blob_url(blob_url)
        
        # Construct the blob URL with SAS token if present
        if sas_token:
            blob_client = BlobClient.from_blob_url(blob_url)
        else:
            blob_client = BlobClient(
                account_url=f"https://{self.account_name}.blob.core.windows.net",
                container_name=container_name,
                blob_name=blob_name,
                credential=self.account_key
            )
            
        print(f"Loading image from: {blob_url}")
        try:
            blob_data = blob_client.download_blob().readall()
            image_content = base64.b64encode(blob_data).decode("utf-8")
            return image_content
        except Exception as e:
            print(f"Error loading image: {str(e)}")
            raise

    def load_images(self, blob_urls):
        print(f"Loading {len(blob_urls)} images from Azure Blob Storage")
        image_contents = []
        for blob_url in blob_urls:
            try:
                image_contents.append(self.load_image(blob_url))
            except Exception as e:
                print(f"Failed to load image {blob_url}: {str(e)}")
                raise
        return image_contents
    
    # upload image to azure blob storage
    def upload_image(self, image_content, container_name, blob_name):
        blob_client = BlobClient(
            account_url=f"https://{self.account_name}.blob.core.windows.net",
            container_name=container_name,
            blob_name=blob_name,
            credential=self.account_key
        )
        blob_client.upload_blob(image_content)
        return blob_client.url
