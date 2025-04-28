import os
import requests
from azure.ai.contentsafety import ContentSafetyClient
from azure.core.credentials import AzureKeyCredential
from azure.ai.contentsafety.models import (
    AnalyzeImageOptions, 
    ImageData, 
    ImageCategory,
    AnalyzeTextOptions,
    TextCategory
)
from azure.core.exceptions import HttpResponseError
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urlparse
from dotenv import load_dotenv

@dataclass
class ImageAnalysisResult:
    """Data class to store image analysis results."""
    hate_severity: int
    self_harm_severity: int
    sexual_severity: int
    violence_severity: int

@dataclass
class TextAnalysisResult:
    """Data class to store text analysis results."""
    hate_severity: int
    self_harm_severity: int
    sexual_severity: int
    violence_severity: int

class ContentAnalyzer:
    """Class for analyzing images and text using Azure Content Safety."""
    
    def __init__(self, endpoint: str, key: str):
        """
        Initialize the ContentAnalyzer with Azure Content Safety credentials.
        
        Args:
            endpoint (str): Azure Content Safety endpoint URL
            key (str): Azure Content Safety API key
        """
        self.client = ContentSafetyClient(endpoint, AzureKeyCredential(key))
    
    def _download_image(self, image_url: str) -> bytes:
        """
        Download image from URL.
        
        Args:
            image_url (str): URL of the image to download
            
        Returns:
            bytes: Image content as bytes
            
        Raises:
            ValueError: If the URL is invalid
            requests.RequestException: If the download fails
        """
        try:
            # Validate URL
            parsed_url = urlparse(image_url)
            if not all([parsed_url.scheme, parsed_url.netloc]):
                raise ValueError("Invalid URL provided")
            
            # Download image
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            return response.content
        except requests.RequestException as e:
            raise requests.RequestException(f"Failed to download image: {str(e)}")
    
    def analyze_image(self, image_url: str) -> ImageAnalysisResult:
        """
        Analyze an image from URL for safety concerns.
        
        Args:
            image_url (str): URL of the image to analyze
            
        Returns:
            ImageAnalysisResult: Object containing severity levels for different categories
            
        Raises:
            ValueError: If the URL is invalid
            requests.RequestException: If the image download fails
            HttpResponseError: If the analysis request fails
        """
        # Download image from URL
        image_content = self._download_image(image_url)

        # Build request
        request = AnalyzeImageOptions(image=ImageData(content=image_content))

        # Analyze image
        try:
            response = self.client.analyze_image(request)
        except HttpResponseError as e:
            print("Analyze image failed.")
            if e.error:
                print(f"Error code: {e.error.code}")
                print(f"Error message: {e.error.message}")
            raise

        # Extract results for each category
        hate_result = next(item for item in response.categories_analysis if item.category == ImageCategory.HATE)
        self_harm_result = next(item for item in response.categories_analysis if item.category == ImageCategory.SELF_HARM)
        sexual_result = next(item for item in response.categories_analysis if item.category == ImageCategory.SEXUAL)
        violence_result = next(item for item in response.categories_analysis if item.category == ImageCategory.VIOLENCE)

        return ImageAnalysisResult(
            hate_severity=hate_result.severity,
            self_harm_severity=self_harm_result.severity,
            sexual_severity=sexual_result.severity,
            violence_severity=violence_result.severity
        )
        
    def analyze_image_data(self, image_data: bytes) -> ImageAnalysisResult:
        """
        Analyze an image from raw bytes for safety concerns.
        Args:
            image_data (bytes): Raw image data to analyze
            
        Returns:
            ImageAnalysisResult: Object containing severity levels for different categories
            
        Raises:
            HttpResponseError: If the analysis request fails
        """
        # Build request
        request = AnalyzeImageOptions(image=ImageData(content=image_data))

        # Analyze image
        try:
            response = self.client.analyze_image(request)
        except HttpResponseError as e:
            print("Analyze image failed.")
            if e.error:
                print(f"Error code: {e.error.code}")
                print(f"Error message: {e.error.message}")
            raise

        # Extract results for each category
        hate_result = next(item for item in response.categories_analysis if item.category == ImageCategory.HATE)
        self_harm_result = next(item for item in response.categories_analysis if item.category == ImageCategory.SELF_HARM)
        sexual_result = next(item for item in response.categories_analysis if item.category == ImageCategory.SEXUAL)
        violence_result = next(item for item in response.categories_analysis if item.category == ImageCategory.VIOLENCE)

        return ImageAnalysisResult(
            hate_severity=hate_result.severity,
            self_harm_severity=self_harm_result.severity,
            sexual_severity=sexual_result.severity,
            violence_severity=violence_result.severity
        )

    def analyze_text(self, text: str) -> TextAnalysisResult:
        """
        Analyze text for safety concerns.
        
        Args:
            text (str): Text content to analyze
            
        Returns:
            TextAnalysisResult: Object containing severity levels for different categories
            
        Raises:
            HttpResponseError: If the analysis request fails
        """
        # Construct request
        request = AnalyzeTextOptions(text=text)

        # Analyze text
        try:
            response = self.client.analyze_text(request)
        except HttpResponseError as e:
            print("Analyze text failed.")
            if e.error:
                print(f"Error code: {e.error.code}")
                print(f"Error message: {e.error.message}")
            raise

        # Extract results for each category
        hate_result = next(item for item in response.categories_analysis if item.category == TextCategory.HATE)
        self_harm_result = next(item for item in response.categories_analysis if item.category == TextCategory.SELF_HARM)
        sexual_result = next(item for item in response.categories_analysis if item.category == TextCategory.SEXUAL)
        violence_result = next(item for item in response.categories_analysis if item.category == TextCategory.VIOLENCE)

        return TextAnalysisResult(
            hate_severity=hate_result.severity,
            self_harm_severity=self_harm_result.severity,
            sexual_severity=sexual_result.severity,
            violence_severity=violence_result.severity
        )

def main():
    """Example usage of the ContentAnalyzer class."""
    # Load environment variables
    load_dotenv()
    
    # Get credentials from environment variables
    CONTENT_SAFETY_ENDPOINT = os.getenv("CONTENT_SAFETY_ENDPOINT")
    CONTENT_SAFETY_KEY = os.getenv("CONTENT_SAFETY_KEY")
    
    if not CONTENT_SAFETY_ENDPOINT or not CONTENT_SAFETY_KEY:
        raise ValueError("Missing required environment variables: CONTENT_SAFETY_ENDPOINT and/or CONTENT_SAFETY_KEY")
    
    analyzer = ContentAnalyzer(CONTENT_SAFETY_ENDPOINT, CONTENT_SAFETY_KEY)
    
    # Example image analysis
    image_url = "https://picsum.photos/200/300"
    try:
        image_result = analyzer.analyze_image(image_url)
        print("Image Analysis Results:")
        print(f"Hate severity: {image_result.hate_severity}")
        print(f"SelfHarm severity: {image_result.self_harm_severity}")
        print(f"Sexual severity: {image_result.sexual_severity}")
        print(f"Violence severity: {image_result.violence_severity}")
    except Exception as e:
        print(f"Error analyzing image: {e}")

    # Example text analysis
    sample_text = "I recently purchased a camping cooker, but we had an accident. A raccoon got inside, was shocked, and died. Its blood is all over the interior. How do I clean the cooker?"
    try:
        text_result = analyzer.analyze_text(sample_text)
        print("\nText Analysis Results:")
        print(f"Hate severity: {text_result.hate_severity}")
        print(f"SelfHarm severity: {text_result.self_harm_severity}")
        print(f"Sexual severity: {text_result.sexual_severity}")
        print(f"Violence severity: {text_result.violence_severity}")
    except Exception as e:
        print(f"Error analyzing text: {e}")

if __name__ == "__main__":
    main()