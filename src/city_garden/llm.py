import os
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langsmith import Client
from langchain_core.tracers import LangChainTracer
from langchain_core.callbacks.manager import CallbackManager
from city_garden.tools.climate import get_monthly_average_temperature, get_monthly_precipitation, get_wind_pattern

load_dotenv()
#verify env variables
#print(f"AZURE_MODEL_NAME: {os.environ['AZURE_MODEL_NAME']}")
#print(f"AZURE_ENDPOINT: {os.environ['AZURE_OPENAI_ENDPOINT']}")

llm = AzureChatOpenAI(
    azure_deployment=os.environ["AZURE_MODEL_NAME"],  # or your deployment
    api_version="2024-12-01-preview",  # or your api version
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)
# Set up LangSmith tracing if API key is available
tracing_enabled = os.environ.get("LANGCHAIN_API_KEY") is not None
if tracing_enabled:
    langsmith_client = Client()
    tracer = LangChainTracer(
        project_name=os.environ.get("LANGCHAIN_PROJECT")
    )
    callback_manager = CallbackManager([tracer])
    # Add tracing to the LLM
    llm.callbacks = callback_manager

tools = [get_monthly_average_temperature, get_monthly_precipitation, get_wind_pattern]
llm.bind_tools(tools, parallel_tool_calls=False)
