import argparse
from towel import thinker
from towel.tools import color
from pydantic import BaseModel
import json

def streaming(llm):

    print(color.GRAY_ME + f"\nstreaming" + color.END)
    for chunk in llm.think(messages=[{"role": "user",
                                      "content": "what's the weather like in Tokyo?"}],
                           stream=True):

        print(color.GRAY_LIGHT + f"{chunk}" + color.END, end='', flush=True)
    print("\n")

def not_streaming(llm):

    print(color.GRAY_ME + f"\nnot streaming" + color.END)

    thoughts = llm.think(prompt="what's the weather like in Tokyo?")

    print(color.GRAY_LIGHT + f"{thoughts}" + color.END)

def with_instructor(llm):

    print(color.GRAY_ME + f"\nwith instructor" + color.END)

    class Review(BaseModel):
        feedback: str
        quality_score: float

    review = llm.think(prompt="is there anything wrong with saying that 41 + 1 = 42.0 ?",
                       response_model=Review)

    print(color.GRAY_LIGHT + f"type: {type(review)}, value: {review}" + color.END)

def check_current_weather(location, unit="fahrenheit"):
    """lookup the current weather in a given location"""
    if "tokyo" in location.lower():
        return json.dumps({"location": "Tokyo", "temperature": "10", "unit": unit})
    elif "new york" in location.lower():
        return json.dumps({"location": "San Francisco", "temperature": "72", "unit": unit})
    elif "paris" in location.lower():
        return json.dumps({"location": "Paris", "temperature": "22", "unit": unit})
    else:
        return json.dumps({"location": location, "temperature": "unknown"})

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

def with_tools(llm, tools):

    print(color.GRAY_ME + f"\nwith tools" + color.END)

    thoughts = llm.think(prompt="what's the weather like in Tokyo?",
                         tools=tools)

    ## ^^ returns "DeepThought" which could be dealt with manually
    ## or passed to call_tools to process the response

    print(f"thoughts: {thoughts}")

    called = thinker.call_tools(thoughts,
                                {"check_current_weather": check_current_weather})

    print(color.GRAY_LIGHT + f"{called}" + color.END)

    return {"tools": called}

def main():

    # "llama3:latest"
    # "llama3:70b-instruct-q8_0"
    # "phi3:3.8b-mini-4k-instruct-f16"
    # "phi3:14b-medium-4k-instruct-f16"
    # "gemma2:9b-instruct-fp16"
    # "gemma2:27b-instruct-fp16"

    llm = thinker.from_cli()
    tools = claude_tools

    with_tools(llm, tools)
    with_instructor(llm)
    not_streaming(llm)
    streaming(llm)

if __name__ == '__main__':
    main()
