import time
import json
from typing import Dict, Any, List, Optional, Union, Generator

import ollama

from openai import OpenAI ## for the "instructor" ollama api ¯\_(ツ)_/¯

from pydantic import BaseModel
import instructor

import towel.brain.tools.fun as fun
from .base import Brain, DeepThought, TextThought, ToolUseThought
from towel.tools import color, say, image_path_to_data, squuid

class Ollama(Brain):

    def __init__(self,
                 model: str,
                 url: Optional[str] = "http://localhost:11434",
                 chat: Optional[bool] = False):

        super().__init__(model)

        self.model = model
        self.url = url

        self.is_chat = chat

        self.client = ollama.Client(host=self.url)

        self.iclient = instructor.from_openai(OpenAI(base_url=self.url + "/v1",
                                                     api_key="ollama"),
                                              mode=instructor.Mode.JSON)

    def _to_deep_thought(self,
                         response: Union[Dict[str, Any],
                                         fun.Response],
                         model='local') -> DeepThought:

        # say("ollama thinker", f"raw response: {response}", color.GRAY_DIUM, color.GRAY_ME)

        content: List[Union[TextThought | ToolUseThought]] = []
        thought_id = str(squuid()) # ollama doesn't provide an id for tool calls.. yet

        if isinstance(response, fun.Response):

            stop_reason = 'end_turn'

            if response.text_response:
                content.append(TextThought(text=response.text_response))

            if response.tool_call:
                content.append(ToolUseThought(
                    id=thought_id,
                    name=response.tool_call.tool,
                    input=response.tool_call.args))
                stop_reason = 'tool_use'

            return DeepThought(
                id=thought_id,
                content=content,
                model=model,
                stop_reason=stop_reason
            )
        else:
            # regular ollama response
            content.append(TextThought(text=response['message']['content']))

            return DeepThought(
                id=thought_id,
                content=content,
                tokens_used=response.get('eval_count', 0),
                model=response.get('model', ''),
                stop_reason=response.get('done_reason', '')
            )

    def _think(self,
               messages: Union[List[Dict[str, str]] | str],
               stream: bool,
               model: Optional[str] = None,
               max_tokens: Optional[int] = None,
               temperature: Optional[float] = None,
               tools: Optional[List[Dict[str, Any]]] = None,
               tool_choice: Optional[str] = None,
               response_model: Optional[BaseModel] = None,
               **kwargs) -> Union[Dict[str, Any], DeepThought, Generator[str, None, None]]:

        options = kwargs.pop('options', {})
        if max_tokens is not None:
            options['num_predict'] = max_tokens
        if temperature is not None:
            options['temperature'] = temperature

        is_chat = kwargs.pop('chat', self.is_chat)

        ## instructor needs it to be a list of dict
        ## ollama by itself needs a string
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}] if response_model or tools or is_chat else messages
        elif isinstance(messages, list) and all(isinstance(item, dict) for item in messages):
            messages = messages if response_model or tools or is_chat else json.dumps(messages)
        else:
            raise TypeError(f"\"messages\" must be a string or a list of dictionaries")

        api_kwargs = {
            "model": model or self.model,
            "stream": stream,
            "options": options,
        }

        if is_chat:                # /chat
            api_kwargs.update({
                "messages": messages,
                "format": kwargs.pop('format', ''),
                "keep_alive": kwargs.pop('keep_alive', None),
            })
        else:                      # /generate
            api_kwargs.update({
                "prompt": messages,
                "system": kwargs.pop('system', ''),
                "template": kwargs.pop('template', ''),
                "context": kwargs.pop('context', None),
                "raw": kwargs.pop('raw', False),
                "format": kwargs.pop('format', ''),
                "images": kwargs.pop('images', None),
                "keep_alive": kwargs.pop('keep_alive', None),
            })

        # remove None values to use ollama's defaults
        api_kwargs = {k: v for k, v in api_kwargs.items() if v is not None}

        # add remaining kwargs
        api_kwargs.update(kwargs)

        # if tools:
        #     api_kwargs["tools"] = tools
        # if tool_choice:
        #     api_kwargs["tool_choice"] = tool_choice

        if response_model or tools:

            instructor_kwargs = {
                "model": model or self.model,
                "messages": messages,
                ## "stream": stream,
                "max_tokens": max_tokens,
                "max_retries": kwargs.pop('instructor_retries', 5),
                "temperature": temperature,
                "tools": tools,
                "tool_choice": tool_choice,
                "response_model": response_model,
                **kwargs  # other instructor args
            }
            instructor_kwargs = {k: v for k, v in instructor_kwargs.items() if v is not None}

            if tools:

                prompt = fun.ToolPrompt(tools=tools,
                                        # tool_choice=tool_choice,
                                        )

                instructor_kwargs["messages"] = [{"role": "system", "content": prompt.system},
                                                 *messages,
                                                 {"role": "user", "content": prompt.footer}]
                instructor_kwargs["response_model"] = fun.Response

            ## TODO: convert to a log
            # say("ollama thinker", f"ollama args: {instructor_kwargs}", color.GRAY_DIUM, color.GRAY_ME)

            response = self.iclient.chat.completions.create(**instructor_kwargs)

            return response if response_model else self._to_deep_thought(response, model=model or self.model)
        else:
            api_kwargs["stream"] = stream

            if is_chat:
                make_thoughts = self.client.chat      # type: ignore
            else:
                make_thoughts = self.client.generate  # type: ignore

            if stream:
                def response_generator():
                    for part in make_thoughts(**api_kwargs):
                        if is_chat:
                            yield part['message']['content']   # type: ignore
                        else:
                            yield part['response']             # type: ignore
                return response_generator()
            else:
                if is_chat:
                    response = make_thoughts(**api_kwargs)
                else:
                    ## uniform it with the /chat response
                    response = make_thoughts(**api_kwargs)
                    response['message'] = {'role': 'assistant',
                                           'content': response.pop('response')}

                return self._to_deep_thought(response)
