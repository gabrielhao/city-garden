""" 
This class is a tool class for city garden application to get the weather data for the city.
this is a langGraph tool class, to call the open-meteo api to get the weather data for the city. 
It get monthly average temperature, monthly rain fall, wind pattern of the location.
https://open-meteo.com/
"""

from langchain_core.tools import tool
import requests
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry

API_URL = "https://archive-api.open-meteo.com/v1/archive"

@tool
def get_monthly_average_temperature(latitude: float, longitude: float) -> str:
    """Get the monthly average temperature of 2024 for the location.

    Args:
        latitude: float
        longitude: float

    Returns:
        str: The monthly average temperature of 2024 for the location.
    """
    print(f"Getting monthly average temperature for {latitude}, {longitude}")
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "daily": "temperature_2m_mean",
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(API_URL, params=params)
    
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_temperature_2m_mean = daily.Variables(0).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )}

    daily_data["temperature_2m_mean"] = daily_temperature_2m_mean

    daily_dataframe = pd.DataFrame(data=daily_data)
    print(daily_dataframe)   

    # Now group by month and calculate monthly average
    monthly_avg = daily_dataframe.resample('M', on='date').mean()

    print("\nMonthly Average Temperature Data:")
    print(monthly_avg)

    return monthly_avg

@tool
def get_wind_pattern(latitude: float, longitude: float) -> str:
    """Get the wind pattern for the location.
    Args:
        latitude: float
        longitude: float

    Returns:
        str: The wind pattern for the location.
    """
    print(f"Getting wind pattern for {latitude}, {longitude}")
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "daily": "wind_speed_10m_max",
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(API_URL, params=params)
    
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_wind_speed_10m_max = daily.Variables(0).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )}

    daily_data["wind_speed_10m_max"] = daily_wind_speed_10m_max

    daily_dataframe = pd.DataFrame(data=daily_data)
    print(daily_dataframe)
    
    # Now group by month and calculate monthly average
    monthly_avg = daily_dataframe.resample('M', on='date').mean()
    
    print("\nMonthly Average Wind Speed Data:")
    print(monthly_avg)
    
    return monthly_avg

@tool
def get_monthly_precipitation(latitude: float, longitude: float) -> str:
    """Get the monthly precipitation of 2024 for the location.
    Args:
        latitude: float
        longitude: float

    Returns:
        str: The monthly precipitation of 2024 for the location.
    """
    print(f"Getting monthly precipitation for {latitude}, {longitude}")
    cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
    retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
    openmeteo = openmeteo_requests.Client(session=retry_session)
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "daily": "precipitation_sum",
        "timezone": "Europe/Berlin"
    }
    responses = openmeteo.weather_api(API_URL, params=params)
    
    # Process first location. Add a for-loop for multiple locations or weather models
    response = responses[0]
    print(f"Coordinates {response.Latitude()}°N {response.Longitude()}°E")
    print(f"Elevation {response.Elevation()} m asl")
    print(f"Timezone {response.Timezone()}{response.TimezoneAbbreviation()}")
    print(f"Timezone difference to GMT+0 {response.UtcOffsetSeconds()} s")

    # Process daily data. The order of variables needs to be the same as requested.
    daily = response.Daily()
    daily_precipitation_sum = daily.Variables(0).ValuesAsNumpy()

    daily_data = {"date": pd.date_range(
        start=pd.to_datetime(daily.Time(), unit="s", utc=True),
        end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
        freq=pd.Timedelta(seconds=daily.Interval()),
        inclusive="left"
    )}

    daily_data["precipitation_sum"] = daily_precipitation_sum

    daily_dataframe = pd.DataFrame(data=daily_data)
    print(daily_dataframe)
    
    # Now group by month and calculate monthly average
    monthly_avg = daily_dataframe.resample('M', on='date').mean()
    
    print("\nMonthly Average Precipitation Data:")
    print(monthly_avg)
    
    return monthly_avg