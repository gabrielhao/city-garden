from city_garden.graph_builder import build_garden_graph
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
from city_garden.garden_state import GardenState
from city_garden.services.image_loader import AzureImageLoader
from city_garden.services.content_safety import ContentAnalyzer

def main():
    
    # Load images
    image_urls = [            
        "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-1.jpeg",
        "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-2.jpeg",
    #    "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-3.jpeg"
    #    "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-4.jpeg",
    ]
    
    image_loader = AzureImageLoader(
            account_name=os.environ["AZURE_STORAGE_ACCOUNT_NAME"],
            account_key=os.environ["AZURE_STORAGE_ACCOUNT_KEY"]
        )
    garden_image_contents = image_loader.load_images(image_urls)
    
    # Guard against illegal images
    if len(garden_image_contents) == 0:
        raise ValueError("No images loaded")
    
    # Check content safety
    content_analyzer = ContentAnalyzer(
        endpoint=os.environ["AZURE_CONTENT_SAFETY_ENDPOINT"],
        key=os.environ["AZURE_CONTENT_SAFETY_KEY"]
    )
    
    for image_content in garden_image_contents:
        analysis_result = content_analyzer.analyze_image_data(image_content)
        if analysis_result.hate_severity > 0.5 or analysis_result.self_harm_severity > 0.5 or analysis_result.sexual_severity > 0.5 or analysis_result.violence_severity > 0.5:
            raise ValueError("Content safety check failed")
    
    
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
        style_preferences="Ornamental plants",
        plant_recommendations=[],
        location="Berlin, Germany",
        latitude=52.52,
        longitude=13.405,
        images=garden_image_contents,
        messages=[]
    )
    
    # Run the graph
    final_state = graph.invoke(initial_state)
    
    # Print the final output
    print("\n=== FINAL GARDEN DESIGN REPORT ===\n")
    if final_state.get("final_output"):
        print(final_state["final_output"])
    else:
        print("No garden design report available. The compliance check may have failed.")
    
    # Print plant recommendations
    print("\n=== PLANT RECOMMENDATIONS ===\n")
    if final_state.get("plant_recommendations"):
        print(final_state["plant_recommendations"])
    else:
        print("No plant recommendations available. The compliance check may have failed.")


if __name__ == "__main__":
    main()







