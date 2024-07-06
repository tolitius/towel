import argparse, os
from dotenv import load_dotenv
import json

import towel.thinker as thinker
from towel.base import towel, intel, tow
from towel.tools import color
from towel.toolbox.web import search_web

# reference implementation of anthropic / openai / mistral function calling
# w/ @gonnie

def check_current_weather(location, unit="fahrenheit"):
    """Get the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "new york" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

# add check_current_weather to the list of tools LLM can elect to use depending on a prompt
# different providers have different formats for tools ¯\_(ツ)_/¯

claude_tools = [
      {
        "name": "check_current_weather",
        "description": "checks the current weather in a given location",
        "input_schema": {
          "type": "object",
          "properties": {
            "location": {
              "type": "string",
              "description": "The city and state, e.g. New York, NY"
            },
            "unit": {
              "type": "string",
              "enum": ["celsius", "fahrenheit"],
              "description": "The unit of temperature to return, e.g. celsius or fahrenheit"
            }
          },
          "required": ["location"]
        }
      }]

gpt_tools = [
    {
        "type": "function",
        "function": {
            "name": "check_current_weather",
            "description": "Checks the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA",
                    },
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

@towel(prompts={'check weather': "what's the weather like in {location}?"})
def check_weather(location):

    llm, prompts, tools, *_ = tow()

    prompt = prompts['check weather'].format(location=location)

    thoughts = llm.think(prompt=prompt,
                         tools=tools)

    print(color.GRAY_ME + f"deep thoughts: {thoughts}" + color.END)
    ## ^^ returns "DeepThought" which could be dealt with manually
    ## or passed to call_tools to process the response

    called = thinker.call_tools(thoughts,
                                {"check_current_weather": check_current_weather})

    print(color.GRAY_ME + f"{called}" + color.END)

    return called


# usage:
# $ poetry run python hyperland/function_caller.py

def main():

    # "llama3:latest"
    # "llama3:70b-instruct-q8_0"
    # "phi3:3.8b-mini-4k-instruct-f16"
    # "phi3:14b-medium-4k-instruct-f16"
    # "gemma2:9b-instruct-fp16"
    # "gemma2:27b-instruct-fp16"

    llm = thinker.from_cli()
    tools = claude_tools

    with intel(llm=llm,
               tools=tools):
        weather = check_weather("Tokyo")

    print(color.GRAY_VERY_LIGHT + f"weather: {weather[0]['result']}" + color.END)

if __name__ == '__main__':
    main()
