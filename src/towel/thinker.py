import argparse

from typing import Any, Dict, List
from .tools import color
from .brain.base import DeepThought, ToolUseThought, TextThought

from .brain.claude import Claude
from .brain.ollama import Ollama

def call_tools(deep_thought: DeepThought,
               tools) -> List[Dict[str, Any]]:
    """
    process the DeepThought response, calling tools if necessary

    tools is a {name: function} dictionary
    """
    if deep_thought.stop_reason != "tool_use":
        return []

    tool_results = []

    for thought in deep_thought.content:
        if isinstance(thought, ToolUseThought):
            tool_function = tools.get(thought.name, None)
            if tool_function is None:
                tool_results.append({
                    "tool_id": thought.id,
                    "tool_name": thought.name,
                    "input": thought.input,
                    "error": f"function '{thought.name}' not found"
                })
            else:
                try:
                    ## TODO: log vs. print
                    print(color.GRAY_DIUM + f"calling tool: {thought.name}" + color.END)
                    result = tool_function(**thought.input)
                    tool_results.append({
                        "tool_id": thought.id,
                        "tool_name": thought.name,
                        "input": thought.input,
                        "result": result
                    })
                except Exception as e:
                    tool_results.append({
                        "tool_id": thought.id,
                        "tool_name": thought.name,
                        "input": thought.input,
                        "error": str(e)
                    })

    return tool_results

def _parse_args():
    parser = argparse.ArgumentParser(description="thinking with a model")
    parser.add_argument('--provider', '-p',
                        choices=['ollama', 'anthropic', 'chatgpt', 'replicate'],
                        default='ollama',
                        help="provider for the model")
    parser.add_argument('--model', '-m',
                        required=True,
                        help="model to do thinking with")

    return parser.parse_args()

def from_cli():

    ## foo.py -m llama3:latest
    ## bar.py -p anthropic -m claude-3-haiku-20240307

    args = _parse_args()

    providers = {
        'ollama':      Ollama(model=args.model),
        'anthropic':   Claude(model=args.model),
        # 'openai':    OpenAI(model=args.model),
        # 'replicate': Replicate(model=args.model)
        }

    brain = providers[args.provider]
    print(color.GRAY_MEDIUM + f"{brain}" + color.END)

    return brain

def serialize_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    "some APIs won't take ToolUseThought, TextThought objects, so we need to serialize"
    ## TODO: think of adding built in serialization to the pydantic models
    def serialize_item(item: Any) -> Any:
        if isinstance(item, (TextThought, ToolUseThought)):
            return item.dict()
        elif isinstance(item, dict):
            return {k: serialize_item(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [serialize_item(i) for i in item]
        else:
            return item

    serialized_messages = []
    for message in messages:
        serialized_message = {
            'role': message['role'],
            'content': serialize_item(message['content'])
        }
        serialized_messages.append(serialized_message)

    return serialized_messages


## make thinker help planning instead of Clique .carry_out
##      i.e. single interface for thinking and planning

# from goonies.clique import Clique, Step, Pin, Route
# from goonies.brain.base import Brain

# def plan(steps: List[Union[Step, Pin, Route]]
#          llm: Brain,
#          config: Optional[Dict[str, Brain]] = None):
#     return Clique().carry_out(steps)
