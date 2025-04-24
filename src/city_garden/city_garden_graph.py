from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from typing import Dict, Any, List, TypedDict, Annotated
from .garden_state import GardenState
from .tools.climate import get_climate_data
from .services.image_loader import load_images
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
from langchain_openai import ChatOpenAI
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
# [TODO] add images
# [TODO] add langsmith tracing
# [TODO] add tool binding

class CityGardenGraph(StateGraph):
    def __init__(self, llm: BaseChatModel):
        """
        Initialize the CityGardenGraph with an LLM.
        
        Args:
            llm: A language model for generating garden analysis
        """
        super().__init__()

        load_dotenv()

        self.llm = ChatOpenAI(model=os.environ["GITHUB_MODEL_NAME"], base_url=os.environ["GITHUB_ENDPOINT"], api_key=os.environ["GITHUB_TOKEN"])
        

        # Add the 4 parallel nodes
        self.add_node("analyze_garden_conditions", self.analyze_garden_conditions)
        self.add_node("get_environment_factors", self.get_environment_factors)
        self.add_node("analyze_wind_pattern", self.analyze_wind_pattern)
        self.add_node("get_style_preferences", self.get_style_preferences)
        
        # Add a join node to combine results
        self.add_node("join_results", self.join_results)

        # Add a node to generate final output
        self.add_node("generate_final_output", self.generate_final_output)
        
        # Define the parallel flow
        self.add_edge(START, "analyze_garden_conditions")
        self.add_edge(START, "get_environment_factors")
        self.add_edge(START, "analyze_wind_pattern")
        self.add_edge(START, "get_style_preferences")
        
        # Connect all nodes to the join node
        self.add_edge("analyze_garden_conditions", "join_results")
        self.add_edge("get_environment_factors", "join_results")
        self.add_edge("analyze_wind_pattern", "join_results")
        self.add_edge("get_style_preferences", "join_results")
        
        # Connect join node to final output
        self.add_edge("join_results", "generate_final_output")
        self.add_edge("generate_final_output", END)
    
    @add_messages
    def analyze_garden_conditions(self, state: GardenState) -> GardenState:
        """
        Node 1: Analyze garden conditions based on time and images.
        Sets sun_exposure, micro_climate, hardscape_elements, and plant_inventory.
        """
        # Get garden information from LLM
        system_prompt = """
        You are a garden expert. Analyze the garden conditions based on the provided information.
        Return a JSON object with the following fields:
        - sun_exposure: Describe the sun exposure (e.g., "Full sun", "Partial shade")
        - micro_climate: Describe the micro climate conditions
        - hardscape_elements: List the hardscape elements present
        - plant_inventory: List the plants currently in the garden
        """
        
        # [TODO] In a real implementation, this would use actual garden images and time of day when the images were taken.
        # For now, we'll use a placeholder description
        # garden_description = "The garden is a small urban space with a concrete patio, wooden fence, and brick wall. It receives about 4-6 hours of direct sunlight in the morning. The area is affected by the urban heat island effect."
        image_urls = [            
            "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-1.jpeg",
            "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-2.jpeg",
            "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-3.jpeg",
            "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-4.jpeg",
            "https://hackthonhub6837342568.blob.core.windows.net/images/example-2-balcony-5.jpeg"
        ]
        garden_images = load_images(image_urls)
        # [TODO] Add images and time of day to the prompt
        time_of_day = "16:00"

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(
                content=[
                    {"type": "text", "text": "Analyze this garden"},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{garden_images}"},
                    }
                ]
            )
        ]
        
        response = self.llm.invoke(messages)
        response_content = response.content
        
        # Parse the response (in a real implementation, this would be more robust)
        # For simplicity, we'll extract the information from the text
        if "sun_exposure" in response_content:
            state["sun_exposure"] = self._extract_value(response_content, "sun_exposure")
        else:
            state["sun_exposure"] = "None, no inpput information"
            
        if "micro_climate" in response_content:
            state["micro_climate"] = self._extract_value(response_content, "micro_climate")
        else:
            state["micro_climate"] = "None, no inpput information"
            
        if "hardscape_elements" in response_content:
            state["hardscape_elements"] = self._extract_value(response_content, "hardscape_elements")
        else:
            state["hardscape_elements"] = "None, no inpput information"
            
        if "plant_inventory" in response_content:
            state["plant_iventory"] = self._extract_value(response_content, "plant_inventory")
        else:
            state["plant_iventory"] = "None currently, new garden"
        
        # Add a message about the analysis
        state["messages"].append({
            "role": "assistant",
            "content": f"I've analyzed your garden conditions based on the provided information. {response_content}"
        })
        
        return state
    
    @add_messages
    def get_environment_factors(self, state: GardenState) -> GardenState:
        """
        Node 2: Get environment factors based on location using OpenWeatherMap API.
        """
        # [TODO] Get city from input
        city = state.get("city", "Berlin")
        
        # Get climate data from API
        climate_data = get_climate_data(city)
        
        # Get additional environment analysis from LLM
        system_prompt = """
        You are a climate expert. Analyze the climate data and provide insights about how it affects gardening.
        Focus on temperature, precipitation, humidity, and seasonal changes.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this climate data for gardening: {climate_data}")
        ]
        
        response = self.llm.invoke(messages)
        
        # Combine API data with LLM analysis
        state["environment_factors"] = f"{climate_data}\n\nLLM Analysis: {response.content}"
        
        # Add a message about the environment factors
        state["messages"].append({
            "role": "assistant",
            "content": f"I've analyzed the climate data for {city}. {response.content}"
        })
        
        return state
    
    @add_messages
    def analyze_wind_pattern(self, state: GardenState) -> GardenState:
        """
        Node 3: Analyze wind pattern based on compass information and images.
        """
        # Get wind information from state or use default
        wind_info = state.get("wind_info", "The garden is exposed to moderate winds from the northwest, which are strongest in the afternoon.")
        
        # Get wind analysis from LLM
        system_prompt = """
        You are a wind expert. Analyze the wind patterns and provide insights about how they affect gardening.
        Consider wind direction, strength, and seasonal variations.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this wind information for gardening: {wind_info}")
        ]
        
        response = self.llm.invoke(messages)
        
        state["wind_pattern"] = response.content
        
        # Add a message about the wind pattern
        state["messages"].append({
            "role": "assistant",
            "content": f"I've analyzed the wind patterns in your garden. {response.content}"
        })
        
        return state
    
    @add_messages
    def get_style_preferences(self, state: GardenState) -> GardenState:
        """
        Node 4: Get style preferences directly from user input.
        """
        # Get style preferences from state or use default
        user_style = state.get("style_preference", "Modern minimalist with native plants")
        
        # Get style analysis from LLM
        system_prompt = """
        You are a garden design expert. Analyze the style preferences and provide insights about how to implement them.
        Consider plant selection, layout, and design elements that match the style.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyze this style preference for gardening: {user_style}")
        ]
        
        response = self.llm.invoke(messages)
        
        state["style_preferences"] = response.content
        
        # Add a message about the style preferences
        state["messages"].append({
            "role": "assistant",
            "content": f"I've analyzed your style preferences. {response.content}"
        })
        
        return state
    
    @add_messages
    def join_results(self, state: GardenState) -> GardenState:
        """
        Join node that combines results from all parallel nodes.
        """
        # Get garden design recommendation from LLM
        system_prompt = """
        You are a garden design expert. Based on all the garden information provided, create a comprehensive garden design recommendation.
        Include plant suggestions, layout ideas, and design elements that match the style preferences and work with the environmental conditions.
        """
        
        garden_info = f"""
        Sun exposure: {state.get('sun_exposure', 'Not analyzed')}
        Micro climate: {state.get('micro_climate', 'Not analyzed')}
        Hardscape elements: {state.get('hardscape_elements', 'Not analyzed')}
        Plant inventory: {state.get('plant_iventory', 'Not analyzed')}
        Environment factors: {state.get('environment_factors', 'Not analyzed')}
        Wind pattern: {state.get('wind_pattern', 'Not analyzed')}
        Style preferences: {state.get('style_preferences', 'Not analyzed')}
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Create a garden design recommendation based on this information: {garden_info}. 
                         As a part of the output, provide a list of plants that are recommended for the garden in a json format with key 'plant_recommendations' and value as a list of plant names.")
        ]
        
        response = self.llm.invoke(messages)

        # Parse the response
        response_content = response.content
        if "plant_recommendations" in response_content:
            state["plant_recommendations"] = self._extract_value(response_content, "plant_recommendations")
        else:
            state["plant_recommendations"] = "None, no information"
        
        # Add a summary message
        state["messages"].append({
            "role": "assistant",
            "content": "I've completed the analysis of your garden. Here's a summary of what I found:"
        })
        
        state["messages"].append({
            "role": "assistant",
            "content": garden_info
        })
        
        # Add the design recommendation
        state["messages"].append({
            "role": "assistant",
            "content": f"Based on all this information, here's my garden design recommendation:\n\n{response.content}"
        })
        
        return state
    
    @add_messages
    def generate_final_output(self, state: GardenState) -> GardenState:
        """
        Node 5: Generate final output. Take garden_info and plant_recommendations and create a final output. 
        Final output should be a structured report with the following sections:
        - Introduction
        - Garden Analysis
        - Plant Recommendations
        - Design Recommendations
        - Conclusion
        """
        # Get garden information from state
        garden_info = f"""
        Sun exposure: {state.get('sun_exposure', 'Not analyzed')}
        Micro climate: {state.get('micro_climate', 'Not analyzed')}
        Hardscape elements: {state.get('hardscape_elements', 'Not analyzed')}
        Plant inventory: {state.get('plant_iventory', 'Not analyzed')}
        Environment factors: {state.get('environment_factors', 'Not analyzed')}
        Wind pattern: {state.get('wind_pattern', 'Not analyzed')}
        Style preferences: {state.get('style_preferences', 'Not analyzed')}
        """
        
        # Get plant recommendations
        plant_recommendations = state.get('plant_recommendations', 'No plant recommendations available')
        
        # Create a prompt for the LLM to generate a structured report
        system_prompt = """
        You are a professional garden designer. Create a comprehensive garden design report based on the provided information.
        The report should be well-structured with the following sections:
        
        1. Introduction - A brief overview of the garden project
        2. Garden Analysis - Detailed analysis of the garden conditions
        3. Plant Recommendations - List and description of recommended plants
        4. Design Recommendations - Layout and design elements
        5. Conclusion - Summary and next steps
        
        Make the report professional, informative, and actionable. Include specific details and recommendations.
        """
        
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"""
            Create a comprehensive garden design report based on the following information:
            
            GARDEN INFORMATION:
            {garden_info}
            
            PLANT RECOMMENDATIONS:
            {plant_recommendations}
            
            Please structure the report with the sections mentioned in the system prompt.
            """)
        ]
        
        # Generate the final report
        response = self.llm.invoke(messages)
        final_report = response.content
        
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
    
    def _extract_value(self, text: str, key: str) -> str:
        """Extract a value from a JSON-like string."""
        try:
            # Simple extraction - in a real implementation, this would use proper JSON parsing
            start = text.find(f'"{key}"') + len(f'"{key}"') + 2
            end = text.find('"', start)
            if start > -1 and end > -1:
                return text[start:end]
            return ""
        except:
            return ""
    
    @add_messages
    def __call__(self, state: GardenState) -> GardenState:
        """
        Execute the graph with the given state.
        """
        # Initialize messages if not present
        if "messages" not in state:
            state["messages"] = []
            
        # Run the graph
        return self.run(state)


if __name__ == "__main__":
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
        wind_info="The garden is exposed to moderate winds from the northwest, which are strongest in the afternoon."
    )
    
    # Run the graph
    final_state = graph(initial_state)
    
    # Print the final output
    print("\n=== FINAL GARDEN DESIGN REPORT ===\n")
    print(final_state["final_output"])
    
    # Print plant recommendations
    print("\n=== PLANT RECOMMENDATIONS ===\n")
    print(final_state["plant_recommendations"])

