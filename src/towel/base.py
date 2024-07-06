from functools import wraps
from contextvars import ContextVar
from contextlib import contextmanager

_towel_context = ContextVar('towel_context', default={})

def towel(llm=None,
          iam=None,
          tools=[],
          feedback=None,
          prompts={}):

    def decorator(func):

        # 'iam' to the function's fully qualified name if not provided
        initial_iam = iam if iam is not None else f"{func.__module__}.{func.__name__}"

        @wraps(func)
        def wrapper(*args, **kwargs):
            with intel(llm=llm,
                       iam=initial_iam,
                       tools=tools,
                       feedback=feedback,
                       prompts=prompts):
                return func(*args, **kwargs)

        return wrapper
    return decorator

@contextmanager
def intel(llm=None,
          iam=None,
          tools=[],
          feedback=None,
          prompts={}):
    current_context = _towel_context.get()
    new_context = {
        'llm': llm if llm is not None else current_context.get('llm'),
        'iam': iam if iam is not None else current_context.get('iam'),
        'tools': tools if tools else current_context.get('tools', []),
        'feedback': feedback if feedback is not None else current_context.get('feedback'),
        'prompts': prompts if prompts else current_context.get('prompts', {}),
    }
    token = _towel_context.set(new_context)
    try:
        yield new_context
    finally:
        _towel_context.reset(token)

def tow():
    context = _towel_context.get()
    return (context['llm'],
            context['prompts'],
            context['tools'],
            context['feedback'],
            context['iam'])
