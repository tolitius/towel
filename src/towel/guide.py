from typing import Callable, Optional, Dict, Any, List, Union
import inspect
import towel.base as towel
import uuid
from towel.brain.base import Brain
from towel.tools import say, color, LogLevel

class Pin:
    def __init__(self,
                 name: str):
        self.name = name

class Route:
    def __init__(self,
                 condition: Callable[[Dict[str, Any]], str]):
        self.condition = condition

class RouterException(Exception):
    def __init__(self,
                 route_condition: Callable,
                 original_error: Exception):
        self.route_condition = route_condition
        self.original_error = original_error
        condition_name = route_condition.__name__ if hasattr(route_condition, '__name__') else 'anonymous'
        super().__init__(f"could not route based on the condition '{condition_name}' due to: {original_error}")

class Step:
    def __init__(self,
                 func: Callable):
        self.func = func
        self.name = func.__name__ if hasattr(func, '__name__') else 'lambda'
        self.additional_inputs: Dict[str, str] = {}

    def add(self, **kwargs):
        self.additional_inputs.update(kwargs)
        return self

class StepExecutionError(Exception):
    def __init__(self,
                 step_name: str,
                 original_error: Exception):
        self.step_name = step_name
        self.original_error = original_error
        super().__init__(f"could not take this step '{step_name}' due to: {original_error}")

class Guide:
    def __init__(self,
                 llm: Brain,
                 tools: Dict[str, Any] = None,
                 log_level: LogLevel = LogLevel.DEBUG):
        self.default_llm = llm
        self.default_tools = tools or {}
        self.log_level = log_level

    def carry_out(self,
                  plan_steps: List[Union[Pin, Step, Route]],
                  plan_id: Optional[str] = None,
                  start_with: Optional[Any] = None) -> Dict[str, Any]:

        if isinstance(start_with, dict):
            stash = start_with
        else:
            stash = {"input": start_with}

        if plan_id is None:
            plan_id = str(uuid.uuid4())

        current_pin = 'start'
        last_result = None
        step_index = 0

        self.trace(f"plan validated and ready to roll...         [Ok]")
        self.trace(f"plan step count..                           [{len(plan_steps)}]")
        self.trace(f"kicking it off with..                       \"{stash}\"\n")

        while current_pin != 'end' and step_index < len(plan_steps):

            task = plan_steps[step_index]
            self.trace(f"next: {step_index}, type: {type(task).__name__}")

            match task:
                case Pin(name=pin_name):
                    self.trace(f"  - looking at pin: {pin_name}")
                    if pin_name == current_pin:
                        current_pin = None
                        self.trace(f"  - going into pin: \"{pin_name}\"")
                    else:
                        self.trace(f"  - skipping pin: {pin_name} (current pin: {current_pin})")
                    step_index += 1

                case Step():
                    self.trace(f"  - reached step: {task.name}")
                    if current_pin is None:
                        try:

                            step_results = self._to_step_results(stash)

                            use_context = {
                                'llm': self.default_llm,
                                'tools': self.default_tools,
                                'plan_id': plan_id,
                                **step_results
                            }

                            self.debug(f"🐾 taking a step \"{task.name}\"")
                            with towel.intel(**use_context):

                                self.trace(f"    - with inputs arguments: {use_context}\n")

                                result = task.func()    ## step function call

                            stash[task.name] = result
                            last_result = result
                            self.trace(f"    - done with step: {task.name}")
                            self.trace(f"    - results: {result}", color.GRAY_MEDIUM)
                        except Exception as e:
                            self.trace(f"  - (!) could not take this step: {task.name}")
                            raise StepExecutionError(task.name, e)
                    else:
                        self.trace(f"  - skipping step: {task.name} (current_pin: {current_pin})")
                    step_index += 1

                case Route():
                    self.trace(f"  - reached route")
                    if current_pin is None:
                        try:
                            new_pin = task.condition(stash)
                            self.debug(f"routing to \"{new_pin}\"📌")
                            self.trace(f"   - based on \"{stash}\"")
                            current_pin = new_pin
                            step_index = 0  # reset to start of plan to find the new pin
                        except Exception as e:
                            self.error(f"(!) could not route based on the condition")
                            self.error(f"    - stash: {stash}")
                            raise RouterException(task.condition, e)
                    else:
                        self.trace(f"  - skipping route (current pin: {current_pin})")
                        step_index += 1

                case _:
                    self.trace(f"  - encountered unknown task type: {type(task)}")
                    step_index += 1

            self.trace(f"  - ready for the next step: {current_pin}, step index: {step_index}")

        self.debug(f"✔️ all done\n")
        return stash

    def _to_step_results(self,
                         stash: Dict[str, Any]) -> Dict[str, Any]:

        step_results = {}
        collisions = []

        for step_name, step_result in stash.items():

            if isinstance(step_result, dict):

                for key, value in step_result.items():
                    if key in step_results:
                        collisions.append((key, step_name))
                    step_results[key] = value
                    # full_context[f"{step_name}_{key}"] = value
            else:
                # if a step result is not a dict, we include it directly
                step_results[step_name] = step_result

        if collisions:
            self.warn("argument name collisions detected:")
            for key, step in collisions:
                self.warn(f"  - argument '{key}' value is overwritten by the later step '{step}'")

        return step_results


    ## TODO: for now handrolled print with ASCII colors, later use python logging
    def log(self,
            message,
            message_color):
        say("guide",
            message,
            color.GRAY_DIUM,
            message_color,
            False)

    def trace(self,
              message,
              message_color = color.GRAY_ME):
        if self.log_level == LogLevel.TRACE:
            self.log(message, message_color)

    def debug(self,
              message,
              message_color = color.GRAY_MEDIUM):
        if self.log_level == LogLevel.DEBUG or self.log_level == LogLevel.TRACE:
            self.log(message, message_color)

    def warn(self,
             message,
             message_color = color.YELLOW):  ## find orange color
        self.log(message, message_color)

    def error(self,
              message,
              message_color = color.RED):
        self.log(message, message_color)


def step(func: Callable) -> Step:
    return Step(func)

def pin(name: str) -> Pin:
    return Pin(name)

def route(condition: Callable[[Dict[str, Any]], str]) -> Route:
    return Route(condition)

def plan(steps: List[Union[Pin, Step, Route]]) -> List[Union[Pin, Step, Route]]:
    if not isinstance(steps[0], Pin) or steps[0].name != 'start':
        steps.insert(0, Pin('start'))
    if not isinstance(steps[-1], Pin) or steps[-1].name != 'end':
        steps.append(Pin('end'))
    return steps
