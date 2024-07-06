import time
from typing import Dict, Any, List, Optional, Union, Generator

from anthropic import Anthropic
from pydantic import BaseModel
import instructor

from .base import Brain, DeepThought, TextThought, ToolUseThought

class Claude(Brain):

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None):

        super().__init__(api_key, model)

        self.client = Anthropic(api_key=self.api_key)

        self.iclient = instructor.from_anthropic(
                self.client,
                mode=instructor.Mode.ANTHROPIC_JSON)

        self.model = model

    def _to_deep_thought(self,
                         response) -> DeepThought:

        content: List[Union[TextThought | ToolUseThought]] = []

        for content_block in response.content:
            if isinstance(content_block, dict):
                if content_block.get('type') == 'text':
                    content.append(TextThought(text=content_block['text']))
                elif content_block.get('type') == 'tool_use':
                    content.append(ToolUseThought(id=content_block.get('id', ''),
                                                  name=content_block['name'],
                                                  input=content_block['input']))
            else:
                if hasattr(content_block, 'text'):
                    content.append(TextThought(text=content_block.text))
                elif hasattr(content_block, 'name') and hasattr(content_block, 'input'):
                    content.append(ToolUseThought(id=getattr(content_block, 'id', ''),
                                                  name=content_block.name,
                                                  input=content_block.input))

        usage = getattr(response, 'usage', None)
        tokens_used = getattr(usage, 'output_tokens', 0) if usage else 0

        return DeepThought(id=getattr(response, 'id', ''),
                           content=content,
                           tokens_used=tokens_used,
                           model=getattr(response, 'model', ''),
                           stop_reason=getattr(response, 'stop_reason', ''))

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

        ## think super method allows a simple "prompt" arg which could be just a string
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        api_kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": 1024 if max_tokens is None else max_tokens,
            "stream": stream,
            **{k: v for k, v in {
                "temperature": temperature,
                "tools": tools,
                "tool_choice": tool_choice,
            }.items() if v is not None},
            **kwargs
        }

        if tools:
            api_kwargs["tools"] = tools
        if tool_choice:
            api_kwargs["tool_choice"] = tool_choice

        if response_model:
            api_kwargs["response_model"] = response_model
            response = self.iclient.messages.create(**api_kwargs)
            return response
        else:
            api_kwargs["stream"] = stream
            if stream:
                def response_generator():
                    for chunk in self.client.messages.create(**api_kwargs):
                        if hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                            yield chunk.delta.text
                        elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'content'):
                            yield chunk.delta.content
                        elif hasattr(chunk, 'content'):
                            yield chunk.content
                return response_generator()
            else:
                response = self.client.messages.create(**api_kwargs)
                return self._to_deep_thought(response)
