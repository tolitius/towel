from functools import wraps
from contextvars import ContextVar
from contextlib import contextmanager
from typing import Any, Dict
import inspect

_towel_context = ContextVar('towel_context', default={})

def towel(llm=None,
          iam=None,
          tools=[],
          prompts={}):

    def decorator(func):

        # 'iam' to the function's fully qualified name if not provided
        whoami = iam if iam is not None else f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            context = _towel_context.get()

            # Update context with towel-specific items
            context.update({
                'llm': llm or context.get('llm'),
                'iam': whoami,
                'tools': tools or context.get('tools', []),
                'prompts': prompts or context.get('prompts', {})
            })

            sig = inspect.signature(func)
            context_args = {}

            # handle positional arguments: i.e. when towels used without a Guide / plan
            bound_args = sig.bind_partial(*args)
            context_args.update(bound_args.arguments)

            # Only include arguments that are in the function signature
            for param in sig.parameters:
                if param in context:
                    context_args[param] = context[param]

            # Update with explicitly passed arguments
            context_args.update(kwargs)

            result = func(**context_args)

            # Update context with the result
            if isinstance(result, dict):
                context.update(result)
            else:
                context[func.__name__] = result

            _towel_context.set(context)
            return result
        return wrapper
    return decorator

@contextmanager
def intel(**kwargs):
    token = _towel_context.set(_towel_context.get() | kwargs)
    try:
        yield
    finally:
        _towel_context.reset(token)

def tow():
    context = _towel_context.get()
    return (
        context.get('llm'),
        context.get('prompts', {}),
        context.get('tools', []),
        context.get('iam'),
        {k: v for k, v in context.items() if k not in ['llm', 'iam', 'tools', 'prompts']}
    )
