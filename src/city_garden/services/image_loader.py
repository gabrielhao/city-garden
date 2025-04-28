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
        print(f"Loading image from: {blob_url}")
        blob_data = blob_client.download_blob().readall()
        
        # Debug: Show the image
        # stream = BytesIO(blob_data)
        # image = Image.open(stream)
        # image.show()
        
        image_content = base64.b64encode(blob_data).decode("utf-8")

        return image_content


    def load_images(self, blob_urls):
        print(f"Loading {len(blob_urls)} images from Azure Blob Storage")
        image_contents = []
        for blob_url in blob_urls:
            image_contents.append(self.load_image(blob_url))
        return image_contents
    