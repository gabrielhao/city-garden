# City Garden

A smart garden design assistant that analyzes garden conditions and provides personalized recommendations.

## Overview

City Garden is an AI-powered application that helps urban gardeners design and optimize their garden spaces. It analyzes various factors such as sun exposure, micro-climate, hardscape elements, and environmental conditions to provide tailored plant recommendations and design suggestions.

## Features

- **Garden Analysis**: Analyzes sun exposure, micro-climate, and existing hardscape elements
- **Environmental Factors**: Retrieves climate data based on location
- **Wind Pattern Analysis**: Analyzes wind patterns and their impact on garden design
- **Style Preferences**: Incorporates user style preferences into recommendations
- **Comprehensive Reports**: Generates detailed garden design reports with plant recommendations
- **Garden Visualization**: Generates visual representations of the recommended garden design
- **LangSmith Tracing**: Monitors and debugs the application flow with detailed tracing

## Project Structure

```
city-garden/
├── src/
│   └── city_garden/
│       ├── __init__.py
│       ├── city_garden_graph.py      # Main graph implementation
│       ├── garden_state.py           # State management
│       └── services/
│           ├── image_loader.py       # Azure blob storage image loader
│           └── image_generation.py   # Garden visualization service
│           ├── content_safety.py         # Image/Text safety analysis
├── tests/
│   └── test_city_garden_graph.py     # Tests for the graph
├── .env                               # Environment variables
├── requirements.txt                   # Project dependencies
└── README.md                          # This file
```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/city-garden.git
   cd city-garden
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   # Azure Content Safety API credentials
   CONTENT_SAFETY_ENDPOINT=your_endpoint
   CONTENT_SAFETY_KEY=your_key

   # OpenWeatherMap API credentials
   OPENWEATHERMAP_API_KEY=your_key

   # LangSmith tracing (optional)
   LANGCHAIN_API_KEY=your_key
   LANGCHAIN_PROJECT=city-garden
   LANGCHAIN_TRACING_V2=true

   # Default city for climate data
   DEFAULT_CITY=New York

   # Azure Storage credentials
   AZURE_STORAGE_ACCOUNT_NAME=your_account_name
   AZURE_STORAGE_ACCOUNT_KEY=your_account_key

   # GitHub model credentials
   GITHUB_ENDPOINT=your_endpoint
   GITHUB_MODEL_NAME=your_model_name
   GITHUB_TOKEN=your_token

   # Image Generation API credentials (if applicable)
   IMAGE_GENERATION_API_KEY=your_key
   IMAGE_GENERATION_ENDPOINT=your_endpoint
   ```
   
5. Run the main.py
   ```
   python3 src/main.py
   ```
## Usage

### Running the Garden Graph

```python
from src.city_garden.city_garden_graph import CityGardenGraph
from src.city_garden.garden_state import GardenState
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the LLM
llm = ChatOpenAI(
    model=os.environ["GITHUB_MODEL_NAME"], 
    base_url=os.environ["GITHUB_ENDPOINT"], 
    api_key=os.environ["GITHUB_TOKEN"]
)

# Create the graph
graph = CityGardenGraph(llm)

# Initialize the state
initial_state = GardenState(
    sun_exposure="",
    micro_climate="",
    hardscape_elements="",
    plant_iventory="",
    environment_factors="",
    wind_pattern="",
    style_preferences="",
    plant_recommendations=[],
    messages=[],
    city=os.environ.get("DEFAULT_CITY", "New York"),
    style_preference="Modern minimalist with native plants",
    wind_info="The garden is exposed to moderate winds from the northwest."
)

# Run the graph
final_state = graph(initial_state)

# Access the results
print(final_state["final_output"])
print(final_state["plant_recommendations"])
```

### Loading Images from Azure Blob Storage

```python
from src.city_garden.services.image_loader import AzureImageLoader
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the image loader
image_loader = AzureImageLoader(
    account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
    account_key=os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
)

# Load a single image
image = image_loader.load_image("https://your-storage-account.blob.core.windows.net/container/image.jpg")

# Load multiple images
images = image_loader.load_images([
    "https://your-storage-account.blob.core.windows.net/container/image1.jpg",
    "https://your-storage-account.blob.core.windows.net/container/image2.jpg"
])
```

### Garden Visualization

The application can generate visual representations of the recommended garden design based on the analysis and plant recommendations. The visualization is created using the garden image description generated by the LLM and processed through an image generation service.

```python
from src.city_garden.services.image_generation import generate_image

# Generate and display the garden visualization
garden_image = generate_image(garden_description)
garden_image.show()
```

The visualization helps users better understand how their garden will look with the recommended plants and layout.

### LangSmith Tracing

The application includes LangSmith tracing to monitor and debug the graph execution. To enable tracing:

1. Set up your LangSmith API key in the `.env` file:
   ```
   LANGCHAIN_API_KEY=your_langsmith_api_key
   LANGCHAIN_PROJECT=city-garden
   LANGCHAIN_TRACING_V2=true
   ```

2. The tracing will automatically be enabled when you run the application.

3. View traces in the LangSmith dashboard:
   - Go to https://smith.langchain.com/
   - Navigate to the "city-garden" project
   - View detailed traces of each node execution

## Testing

Run the tests with pytest:

```bash
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Azure Content Safety API for image analysis
- OpenWeatherMap API for climate data
- LangChain for LLM integration
- LangGraph for workflow management
- LangSmith for tracing and monitoring
