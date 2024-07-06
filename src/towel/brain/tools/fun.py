## function calling leaderboard: https://gorilla.cs.berkeley.edu/leaderboard.html

from typing import Dict, Any, List, Optional, Union
from pydantic import BaseModel, Field, root_validator
import json

from .prompt.generic import system_prompt, footer_prompt

class CallTool(BaseModel):
    tool: str = Field(default="", description="The name of the tool to call")
    args: Dict[str, Any] = Field(default_factory=dict, description="{\"name\": value} arguments for the tool")

class Response(BaseModel):
    text_response: str
    tool_call: Optional[CallTool] = None

    @root_validator(pre=True)
    def check_fields(cls, values):
        if 'tool_call' in values and not values.get('text_response'):
            raise ValueError("If 'tool_call' is present, 'text_response' must also be present")
        return values

## for prompt based, not "built in" function calling models
class ToolPrompt:
    def __init__(self,
                 tools: List[Dict[str, Any]]):

        self.system: str = ""
        self.footer: str = ""
        self.tools: List[Dict[str, Any]] = tools
        self._make_prompts()

    def _make_prompts(self):

        self.make_system_prompt()
        self.make_footer_prompt()

    def _tool_spec(self) -> str:
        return "[" + "\n".join([f"{tool}" for tool in self.tools]) + "]"

    def make_system_prompt(self):
        tools = self._tool_spec()
        self.system = system_prompt(tools)

    def make_footer_prompt(self):
        self.footer = footer_prompt()

    def __str__(self) -> str:
        return f"""ToolPrompt:
Tools:
{json.dumps(self.tools, indent=2)}

System Prompt:
{self.system}

Footer Prompt:
{self.footer}
"""


## a specific model will/could override the generic ToolPrompt's prompts with the ones that work for it

# class PhiToolPrompt(ToolPrompt):
#
#     def make_system_prompt(self):
#         # phi based implementation
#         pass
#
#     def make_footer_prompt(self):
#         # phi based implementation for a specific model
#         pass



## TODO: sleep on it, _might_ be useful
def fun_to_spec(fun):
    ## given a function:

    #    @schema(required=["location"])
    #    def check_current_weather(location: str,
    #                              unit: Literal["celsius", "fahrenheit"] = "celsius"):
    #        """
    #        Checks the current weather in a given location.
    #
    #        :param location: The city and state, e.g. New York, NY
    #        :param unit: The unit of temperature to return, e.g. celsius or fahrenheit
    #        """
    #        # implementation

    ## return a spec
    pass


