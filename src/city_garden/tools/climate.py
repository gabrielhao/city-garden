""" 
This class is a tool class for city garden application to get the climate data for the city.
this is a langGraph tool class, to call the openweathermap api to get the climate data for the city.
https://openweathermap.org/api
 """

from langchain_core.tools import tool

@tool
def get_climate_data(city: str) -> str:
    """Get the climate data for the city."""