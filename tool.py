import anthropic
import requests
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Assign the API keys to variables
tomorrow_api_key = os.getenv("TOMORROW_API_KEY")
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def get_weather(location):
    # Define the URL to fetch the weather data from the Tomorrow.io API templating the location and the API key
    url = f"https://api.tomorrow.io/v4/weather/forecast?location={location}&apikey={tomorrow_api_key}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
        data = response.json()
        
        if "data" in data and "timelines" in data["data"] and len(data["data"]["timelines"]) > 0:
            temperature = data["data"]["timelines"][0]["intervals"][0]["values"]["temperature"]
            return f"The current temperature in {location} is {temperature}°C."
        else:
            return f"Unable to retrieve weather data for {location}."
    
    except requests.exceptions.RequestException as e:
        return f"Error occurred while fetching weather data: {str(e)}"

def main():

    # Define the weather tool that can be chosen by Claude to get the current temperature in a given location if the user asks for it
    weather_tool = {
    "name": "get_weather",
    "description": "Get the current temperature in a given location using the Tomorrow.io API. The location should be a valid city name, and the API takes this location variable such as 'London, UK'. The temperature must be returned as a figure in degrees Celsius.",
    "input_schema": {
        "type": "object",
        "properties": {
            "location": {
                "type": "string",
                "description": "The city name, such as London, UK."
            }
        },
        "required": ["location"]
        }
    }

    # Call the Claude API to start a conversation with Claude
    response = client.beta.tools.messages.create(
        model="claude-3-opus-20240229",
        max_tokens=1024,
        tools=[weather_tool],
        # Example user message to trigger the tool, you could expand this code by moving this to a command-line input so that the user can ask for the weather in any location
        messages=[{"role": "user", "content": "What's the weather like in London?"}],
    )

    # Print thinking of Claude
    print(response)

    # Check if Claude decided to use the tool
    if response.stop_reason == "tool_use":
        tool_use = next((content for content in response.content if content.type == "tool_use"), None)
        if tool_use:
            # Extract the tool input
            tool_input = tool_use.input
            location = tool_input["location"]

            # Call the get_weather function with the extracted location
            weather_result = get_weather(location)

            # Continue the conversation by providing the tool result
            tool_result_response = client.beta.tools.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1024,
                messages=[
                    {"role": "user", "content": "What's the weather like in London?"},
                    {"role": "assistant", "content": f'<tool_result tool_use_id="{tool_use.id}">{weather_result}</tool_result>'},
                ],
            )

            # Print workings of the tool
            print(tool_result_response)

             # Extract and print out the weather result
            for content in tool_result_response.content:
                if content.type == "text":
                    print(content.text)

if __name__ == "__main__":
    main()
