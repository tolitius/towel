from abc import ABC, abstractmethod
import os
from typing import Dict, Any, List, Optional, Union, Generator, Literal
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import logging

class TextThought(BaseModel):
    text: str
    type: Literal["text"] = "text"

class ToolUseThought(BaseModel):
    id: str
    name: str
    input: Dict[str, Any]
    type: Literal["tool_use"] = "tool_use"

class DeepThought(BaseModel):
    id: str
    content: List[Union[TextThought, ToolUseThought]]
    tokens_used: Optional[int] = None
    model: str
    stop_reason: str

class Brain(ABC):

    def __init__(self,
                 api_key: Optional[str] = None,
                 model: Optional[str] = None):

        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.DEBUG)

        env_path = os.path.join(os.getcwd(), '.env')
        load_dotenv(dotenv_path=env_path)

        self.api_key = api_key
        self.model = model

    def __str__(self):
        if hasattr(self, 'model'):
            return f"{self.__class__.__name__} 🧠 {self.model} ✅"
        else:
            return f"{self.__class__.__name__} 🧠"

    def think(self,
              messages: Optional[Union[List[Dict[str, str]], str]] = None,
              stream: Optional[bool] = False,
              prompt: Optional[str] = None,
              model: Optional[str] = None,
              max_tokens: Optional[int] = None,
              temperature: Optional[float] = None,
              tools: Optional[List[Dict[str, Any]]] = None,
              tool_choice: Optional[str] = None,
              response_model: Optional[BaseModel] = None,
              **kwargs) -> Union[Dict[str, Any], DeepThought, Generator[str, None, None]]:

        if not model and not self.model:
            raise ValueError("\"model\" is missing, and must be specified either in the constructor or when calling \"think\"")

        if prompt and messages:
            self.logger.warning("both 'prompt' and 'messages' arguments were provided. 'prompt' will be ignored.")
        elif prompt and not messages:
            messages = prompt
        elif not messages:
            raise ValueError("either 'messages' or 'prompt' must be provided.")

        return self._think(messages,
                           stream,
                           model or self.model,
                           max_tokens,
                           temperature,
                           tools,
                           tool_choice,
                           response_model,
                           **kwargs)

    @abstractmethod
    def _think(self,
               messages: Union[List[Dict[str, str]] | str],
               stream: bool,
               model: str,
               max_tokens: Optional[int],
               temperature: Optional[float],
               tools: Optional[List[Dict[str, Any]]],
               tool_choice: Optional[str],
               response_model: Optional[BaseModel],
               **kwargs) -> Union[Dict[str, Any], DeepThought, Generator[str, None, None]]:
        pass

    @abstractmethod
    def _to_deep_thought(self,
                         response) -> DeepThought:
        pass

# ---- local models

# nous-hermes2:10.7b-solar-q4_0
# nous-hermes2:10.7b-solar-q6_K
# mistral:7b-instruct-v0.2-fp16
# dolphin-mistral:7b-v2.6-dpo-laser-fp16
# mixtral:8x7b-instruct-v0.1-q4_K_M
# deepseek-coder:6.7b-instruct-fp16
# gemma:7b-instruct-fp16
# llama3:8b-instruct-fp16
# ...

# ---- claude models

# claude-3-haiku-20240307
# claude-3-sonnet-20240229
# claude-3-opus-20240229
# claude-3-5-sonnet-20240620
# ...

# ---- chatgpt models

# gpt-3.5-turbo-0125   (16K context window)
# gpt-4-32k
# gpt-4-turbo-preview  (128K context window)
# gpt-4o
# ...

# ---- replicate models

# meta/meta-llama-3-70b-instruct
# ...
