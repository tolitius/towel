> _"a **towel** is about the most massively useful thing an interstellar AI hitchhiker can have"</br>
> -- Douglas Adams_

# towel <img src="docs/img/towel-logo.png" width="75px">
![PyPI](https://img.shields.io/pypi/v/PACKAGE?label=pypi%2042towels)

compose LLM python functions into dynamic, self-modifying plans

```python
space_trip = plan([

    step(pick_planet),

    pin('are_you_ready'),
    step(how_ready_are_you),
    route(lambda result: 'book' if result['how_ready_are_you']['score'] > 95 else 'train'),

    pin('train'),
    step(space_bootcamp),
    route(lambda x: 'are_you_ready'),

    pin('book'),
    step(reserve_spaceship)
])
```

- [why towel](#why-towel)
- [features](#features)
- [how to play](#how-to-play)
  - [install](#install)
    - [run examples](#run-examples)
  - [LLMs with no towels](#llms-with-no-towels)
    - [LLM libraries and frameworks are unnecessary](#llm-libraries-and-frameworks-are-unnecessary)
    - [basics](#basics)
    - [connect to LLM](#connect-to-llm)
    - [ask LLM a question](#ask-llm-a-question)
    - [stream responses from LLM](#stream-responses-from-llm)
    - [use the built in instructor](#use-the-built-in-instructor)
    - [using tools (a.k.a. function calling)](#using-tools-aka-function-calling)
  - [towels](#towels)
    - [@towel, thinker, intel, tow](#towel-thinker-intel-tow)
    - [a more practical example](#a-more-practical-example)
  - [plans](#plans)
    - [vocabulary](#vocabulary)
      - [step](#step)
      - [pin](#pin)
      - [route](#route)
    - [flow and data](#flow-and-data)
    - [executing a plan](#executing-a-plan)
    - [mind maps](#mind-maps)
    - [kick off intel](#kick-off-intel)
  - [making plans](#making-plans)
  - [plans that make plans](#plans-that-make-plans)
- [license](#license)

## why towel

the name comes from the Hitchhiker's Guide to the Galaxy</br>
where [a towel is](https://en.wikipedia.org/wiki/Towel_Day) the most massively useful thing an interstellar AI hitchhiker can have.

this ultimate truth applies to all the universes including the one full of Large Language Models (a.k.a. LLMs)

any Python function wrapped in a `@towel` becomes the most massively useful and unlocks the power of LLMs:

```python
@towel
def find_meaning_of_life():
  llm, *_ = tow()             ## tows llm into this function.. and more
  llm.think("... about it")
```

since this is just a function it can be composed with other LLM, or not, functions leaving it to just Python and you to create things.

but, in case help composing is needed, towel can assist with making plans that use @towels (i.e. these functions):

```python
plan([

  step(find_meaning_of_life),
  route(lambda result: 'conclude' if result['find_meaning_of_life']['confidence'] > 0.8 else 'test meaning'),

  pin('test meaning'),
  step(reality_check),
  route(lambda x: 'find_meaning_of_life'),

  pin('conclude')
])
```

# features

### plan it like you mean it!
- more powerful than chains, simpler than graphs
- self-modifying plans (plans that make plans)
- simple vocabulary: "`step`", "`route`" and "`pin`" for any plan
- mind maps: each step can have its very own LLM
- dynamic routing based on pure functions and step results

### functions over objects
- function compose.. into elegant workflows
- any function can become an LLM: just wrap it in a `@towel`

### function calling / tool use
- one interface for local models and cloud models
- it's great, it's [pydantic](https://github.com/pydantic/pydantic)

### strong LLM response typing
- it's great, it's pydantic
- built-in support for the [instructor](https://github.com/jxnl/instructor) library, enabling structured outputs
- "[DeepThought](https://github.com/tolitius/towel/blob/6caa70312a3715da7adae89149d6d1ab684a2c37/src/towel/brain/base.py#L8-L23)" full with thoughts for non instructor responses

### thread safety
- dynamic `@towel` context handling
- modify context at runtime "`with intel(llm=llm)`"

### multi-model support
- one "`thinker`" API for all
- switch between different LLM providers (Claude, Ollama, etc.)
- extensible to support additional providers via "[Brain](https://github.com/tolitius/towel/blob/6caa70312a3715da7adae89149d6d1ab684a2c37/src/towel/brain/base.py#L25)"

### local models love
- feature parity with cloud models via Ollama integration

# how to play

let's look around and travel them universes one by one. towel by towel.

## install

the "[Answer to the Ultimate Question of Life, the Universe, and Everything](https://simple.wikipedia.org/wiki/42_(answer))" is 42.

hence in order to harness "the power of the towel" we need to install 42 of them:

```bash
pip install 42towels
```

### run examples

there are examples in [docs/examples](docs/examples) that, after "pip install 42towels", can be run as:

```python
$ python ./docs/examples/function_caller.py -p anthropic -m claude-3-haiku-20240307
```
or
```
$ python ./docs/examples/function_caller.py -m llama3:70b  ## will use Ollama by default
```

## LLMs with no towels

### LLM libraries and frameworks are unnecessary

the hidden truth of every LLM library or framework is that most of the time _**you don't need an LLM library or framework**_, because it all comes down to a simple sequence of two steps:

* come up with a question (a.k.a. "a prompt"): e.g. "what is the meaning of life? think step by step"
* call an HTTP API
```bash
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llama3",
  "prompt": "what is the meaning of life? think step by step"
}'
```
that is pretty much it.</br>
you do it over and over again, it would be called a "chat"</br>
you do it with Generative Pre-trained Transformer models, this chat would be called "chat gpt" (i.e. you _own_ chat gpt).

### basics

where libraries can help is _consistency_ and _repeatability_ which really enhances and helps composing things, such as code things.

in the world of LLMs most of these HTTP APIs and their capabilities are very inconsistent, which is why libraries such as [litellm](https://github.com/BerriAI/litellm) and others help a lot.

towel also aims to provide consistency across models, so it is important to understand the basics: simple ways to engage LLMs without `@towel`s or plans.

### connect to LLM

"`thinker`" is the one with the power to connect to LLMs

```python
from towel import thinker

# would connect to Anthropic's Claude LLM
# it would expect you to have an anthropic key exported in .env:
# export ANTHROPIC_API_KEY=sk-an...

llm = thinker.Claude(model="claude-3-haiku-20240307")


# would connect to any local model hosted by Ollama
# it would expect you to have Ollama running at "http://localhost:11434"
# but a different url can be passed in as well

llm = thinker.Ollama(model="llama3:latest")
```

### ask LLM a question

we'll take examples from [docs/examples/thinking.py](docs/examples/thinking.py)

```python
thoughts = llm.think(prompt="what is the meaning of life? think step by step")
```

thinker would return a DeepThought:

```python
>>> type(thoughts)
<class 'towel.brain.base.DeepThought'>
```

which would look like this:

```python
DeepThought(id='9a7a0f12-ffaa-96bd-aa5e-51362dd2c06e',
            content=[TextThought(text='What a profound and complex question! The meaning of life is ...and wondrous journey called existence.',
                                 type='text')],
            tokens_used=820,
            model='llama3:latest',
            stop_reason='stop')
```

so if you are just after the text it can be extracted as:

```python
>>> thoughts.content[0].text
'What a profound and complex questi... called existence.'
```

### stream responses from LLM

two choices:

"manually":
```python
for chunk in llm.think(prompt="what is the meaning of life? think step by step",
                       stream=True):

    print(chunk, end='', flush=True)
```

or with "thinker"'s help:
```python
from towel.tools import stream

stream(llm.think(prompt="what is the meaning of life? think step by step",
                 stream=True),
```

### use the built in instructor

LLMs are not very good at being.. consistent. This is great for creative writing, but not that great for relying on responses to be formatted in a particular way: schema, type, shape, etc..

this is where [instructor](https://github.com/jxnl/instructor) comes in helping to ensure LLM responses are strongly typed

towel has a built in instructor that can be engaged by passing a "`response_model`" argument with the desired typed output

for example:

```python
from pydantic import BaseModel

class MeaningOfLife(BaseModel):
    meaning: str
    confidence_level: float

thoughts = llm.think(prompt="what is the meaning of life? think step by step",
                     response_model=MeaningOfLife)
```

now thinker will rely on instructor to return the response as the MeaningOfLife type:

```python
>>> thoughts
MeaningOfLife(meaning="I'll do my best to help you explore this existential question!...",
              confidence_level=7.5)
```

### using tools (a.k.a. function calling)

quite a popular topic in LLM circles.

this capability is about asking LLM a question, and also providing it a list of well defined tools (functions) LLM can _decide_ to call instead of answering the question, based on its own knowledge.

one important aspect to understand is: LLM does _**not**_ call functions or tools, but merely responds with a tool name (or several) and its arguments.

here is an example.

let's say we have "a tool" that checks the weather (the most frequent tool that is used as an example on this topic):

```python
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
```

LLMs do not have an up-to date knowledge about the weather, hence if we ask an LLM "what's the weather like in Tokyo?", it would not know, and would usually respond what the weather in Tokiyo like at different times of year. but..

this is where tools come handy.

define a tool/function schema:

```python
tools = [
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
```

and pass it to LLM:

```python
thoughts = llm.think(prompt="what's the weather like in Tokyo?",
                     tools=tools)
```

"`thinker`" would help a model to realize it does not "know" the answer to this question and would need to respond with the name of the tool to use and it arguments

and.. it does:

```python
>>> thoughts
DeepThought(id='9a9d2196-55b8-e252-8bfc-d9a82caaaf97',
            content=[TextThought(text='I can check the current weather in Tokyo for you!',
                                 type='text'),
                     ToolUseThought(id='9a9d2196-55b8-e252-8bfc-d9a82caaaf97',
                                    name='check_current_weather',
                                    input={'location': 'Tokyo, Japan', 'unit': 'celsius'},
                                    type='tool_use')],
                     tokens_used=None,
                     model='llama3:latest',
                     stop_reason='tool_use')
```

one thing to pay attention to is the "`stop_reason`", which, in case a model decided to use a tool, would be "`tool_use`"

"`thinker`" has a helper "`call_tools`" function that can unwrap DeepThought and call tools:

```python
>>> thinker.call_tools(thoughts,
...                    {"check_current_weather": check_current_weather})

calling tool: check_current_weather
[{'tool_id': '9a9d2196-55b8-e252-8bfc-d9a82caaaf97',
  'tool_name': 'check_current_weather',
  'input': {'location': 'Tokyo, Japan',
            'unit': 'celsius'},
  'result': '{"location": "Tokyo",
              "temperature": "10",
              "unit": "celsius"}'}]
```
----
the utility of "`thinker`" in all the cases above is **one single API** that would work for local models as well as non local models such as Claude, etc.

## towels

while [this](#llm-libraries-and-frameworks-are-unnecessary) is still very true, an ability to express LLM communication in just functions vs. "raw prompt + HTTP call"s allows for breaking complex problems into smaller pieces, and converting what could otherwise be inconsistent, repetitive sequence of commands, into beautiful function compositions.

let's work step by step to take a single Python function and "LLM enable" it, giving it some warmth by wrapping it in a @towel.

this function expects a JSON formatted article that it will then convert to markdown format: i.e. a normal, every day, programming task:
> _a full example lives in [docs/examples/wrap_it.py](docs/examples/wrap_it.py)._

```python
def convert_json_to_markdown(article: str) -> str:
    parsed = json.loads(article)
    md = []
    md.append(f"# {article.get('title', 'Untitled')}")
    ## ...

    return '\n'.join(md)
```

the problem is of course in corner cases, malformed JSON, adding / removing features, changing spelling, format, etc. as this function does not really generalize well for inputs it is unable to handle.

let's add some warmth to it: wrap it in a @towel:

```python
from towel import thinker, towel, tow, intel

@towel(prompts={"to_markdown": "convert this JSON {article} to markdown"})
def convert_json_to_markdown(article: str) -> str:

  llm, prompts, *_ = tow()
  thought = llm.think(prompts['to_markdown'].format(article=article))

  return thought.content[0].text
```

now as this function is warm (wrapped in a @towel), let's give it a go:

```python
llm = thinker.Ollama(model="llama3:latest")
# or
# llm = thinker.Claude(model="claude-3-haiku-20240307")

with intel(llm=llm):
    markdown = convert_json_to_markdown(json_article)

print(markdown)
```

and we see the exact same markdown that was produced by the first, non LLM, "cold" Python function.</br>
an interesting aspect about this @towel function is that it _generalizes_: it can convert a lot more JSON formats, and handle a lot more corner cases.

you can check out and run [docs/examples/wrap_it.py](docs/examples/wrap_it.py) to experiment with both.

### @towel, thinker, intel, tow

eeny, meeny, miny, moe..

looking at the example above it might not be obvious what "`intel`" and "`tow`" are doing.

"`intel`" is a function that sets up a thread local context for this "convert_json_to_markdown" function run</br>
and, in this case, it sets it up with an extra variable: "`llm`"

```python
with intel(llm=llm):
    markdown = convert_json_to_markdown(json_article)
```

which is later available inside this function via "`tow()`":
```python
@towel(prompts={"to_markdown": "convert this JSON {article} to markdown"})
def convert_json_to_markdown(article: str) -> str:

  llm, prompts, *_ = tow()
  ## ...
```

you can notice that "`tow()`" also makes "`prompts`" accessible.

"`prompts`" are, of course, optional and can be created inside the function, passed in, etc.</br>
at the end this is just a function, so anything Python goes.

### a more practical example

you can see a simple, but much more interesting example in [docs/examples/paper_summarizer.py](docs/examples/paper_summarizer.py)</br>
where a single @towel takes a link to  white paper, pulls it down from the web and does these 3:

```python
@towel(prompts={'main points': 'summarize the main points in this paper',
                'eli5':        'explain this paper like I\'m 5 years old',
                'issues':      'summarize issues that you can identify with ideas in this paper'})
def summarize_paper(url):
  ## ....
```
> [!NOTE]
_more examples in [docs/examples](docs/examples)_

## plans

* LLM communication with "`thinker`"</br>
and
* "`@towel`" function composition

allow towel to empower an LLM, or a collection of LLMs, to _**plan**_ their activities given one or more problems to solve.

### vocabulary

a "plan" is a sequence of steps, routes and pins:

#### step

a step is a single executable unit of a plan. it sounds more than it really is since it is just an arbitrary function, in most cases a @towel function.

example:

```python
from towel import step

def find_meaning_of_life():
  return {"meaning_of_life": 42}

>>> step(find_meaning_of_life)
<towel.guide.Step object at 0x1083e93d0>
```

by itself "`step`" is not very useful, but as a part of a "plan" it is essential.

#### pin

a pin is a marker, or a checkpoint in a plan. it does not do anything besides having an addressable _name_:

```python
from towel import pin

>>> pin("rock and roll")
<towel.guide.Pin object at 0x1083cc7d0>
```

it is later heavily used by "route", as well as it is really useful for debugging a plan flow.

#### route

a route is a conditional unit of a plan. whenever plan flow gets to a route, it runs a condition (i.e. checks things) and depending on that check the flow can be routed to any "pin".

in order to create a route, it needs to be given a function or lambda:

```python
from towel import route

>>> route(lambda result: 'conclude' if result['find_meaning_of_life']['confidence'] > 0.8 else 'test meaning')
<towel.guide.Route object at 0x108696e90>
```

which means:
* go to a "conclude" pin (a pin with name "conclude") iff a result from the "find_meaning_of_life" has a "confidence" key with a value greater than "0.8"
* otherwise go to "test meaning" (a pin with name "test meaning")

### flow and data

let's look a the real plan that is a sequence of steps, pins and routes:

> _a full example lives in [docs/examples/space_trip.py](docs/examples/space_trip.py)_

```python
from towel import step, route, pin, plan

space_trip = plan([

    step(pick_planet),

    pin('are_you_ready'),
    step(how_ready_are_you),
    route(lambda result: 'book' if result['how_ready_are_you']['score'] > 95 else 'train'),

    pin('train'),
    step(space_bootcamp),
    route(lambda x: 'are_you_ready'),

    pin('book'),
    step(reserve_spaceship)
])
```

it starts out with "step(pick_planet)" which would call a function `pick_planet`:

```python
@towel
def pick_planet():
    ## ...
    return {'destination': planets[choice].name}
```

notice that this function returns "destination". internally towel would hold on to the result from this function, and would make it available for all other functions via arguments.

then the flow reaches `pin('are_you_ready')`. it does not nothing, as pins do nothing.

it then moves on to the "step(how_ready_are_you)" which calls a function `how_ready_are_you`:

```python
@towel
def how_ready_are_you(destination):
    ## ...
    return {'score': readiness.score}

```

notice that nothing inside the plan definition is passing any arguments into "how_ready_are_you", but it does take a "destination" argument.<br/>
this destination argument will be passed (by name) from the internal plan context that _remembers all the return values from all the steps_ and makes them available as function arguments.

the flow then looks at the route:

```python
route(lambda result: 'book' if result['how_ready_are_you']['score'] > 95 else 'train')
```

which would:
* route the flow to the `pin('book')` iff the "score" value of the "how_ready_are_you" step is larger than 95
* otherwise it would route to the `pin('train')`

the rest is of the flow uses the exact same concepts

> [!TIP]
> remember to return dictionaries from `@towel` functions that are part of the plan</br>
> as the **_keys_** from those dictionaries then matched to other step function **_arguments_** </br>
> and if it is a match values are bound / arguments are _passed_ by the flow

### executing a plan

as you can see in the example ([docs/examples/space_trip.py](docs/examples/space_trip.py)), a plan is executed by the "`thinker.plan()`" function:

```python
llm = thinker.Ollama(model="llama3:latest")
# llm = thinker.Claude(model="claude-3-haiku-20240307")

trip = thinker.plan(space_trip,
                    llm=llm)

say("trip is booked:", f"{json.dumps(trip['reserve_spaceship'], indent=2)}")
```

### mind maps

since plans have many steps, it might be needed to perform some steps with LLMs that are better suited for it.

by default a plan would execute all the steps with an LLM that was provided to it:

```python
blueprint = make_plan()

thinker.plan(blueprint,
             llm=llama)
```

in case some steps need to be done by different LLMs, a plan takes a "`mind_map`" argument:

```python
thinker.plan(blueprint,
             llm=llama,
             mind_map={"review_stories": claude},
             start_with={"requirements": requirements})
```

all the steps in this plan are going to be performed by a "llama" model, but a "review_stories" step will be done by "claude"

you can look at the full example in [docs/examples/execute_da_plan.py](docs/examples/execute_da_plan.py)<br/>
where a smaller "`llama3 8B`" takes requirements, creates user stories, but "`claude`" is the one who reviews these stories, and provides feedback:

```python
    return plan([

        step(create_stories),

        pin('review'),
        step(review_stories),   ## <<< this step will be done by Claude
        route(lambda result: 'revise' if result['review_stories']['quality_score'] < 0.8 else 'implement'),

        pin('revise'),
        step(revise_stories),
        route(lambda x: 'review'),

        pin('implement'),
        step(implement_code)
])
```

### kick off intel

plan is usually kicked off with initial data: a problem definition or a question

this is done via a "`start_with`" plan argument:

```python
thinker.plan(blueprint,
             llm=llama,
             start_with={"requirements": requirements})
```

and "`requirements`" would most likely be a function argument name in the first step in this plan.

## making plans

plan's clear [vocabulary](#vocabulary) and the fact the plan itself is a data structure enables LLMs to take in a problem<br/>
... and _create a plan_ to solve this problem:

```python
from towel import towel, tow
from towel.type import Plan
from towel.prompt import make_plan

@towel(prompts={'plan': """given this problem: {problem} {make_plan}"""})
def make_da_plan(problem: str):
    llm, prompts, *_ = tow()
    plan = llm.think(prompts['plan'].format(problem=problem,
                                            make_plan=make_plan),
                     response_model=Plan)
    return plan
```

this function takes a problem and creates a plan
> full example is in [docs/examples/make_da_plan.py](docs/examples/make_da_plan.py)

for example, here is a plan Claude created to..

```python
llm = Claude(model="claude-3-haiku-20240307")

with intel(llm=llm):
    plan = make_da_plan("make sure there are no wars")
```
```python
[
  step(analyze_current_global_conflicts),
  step(identify_root_causes),
  step(assess_diplomatic_relations),
  route(lambda result: 'improve_diplomacy' if result['assess_diplomatic_relations']['status'] == 'poor' else 'address_economic_factors'),

  pin('improve_diplomacy'),
  step(organize_peace_talks),
  step(implement_conflict_resolution_strategies),
  route(lambda result: 'address_economic_factors' if result['implement_conflict_resolution_strategies']['success'] else 'reassess_diplomatic_approach'),

  pin('reassess_diplomatic_approach'),

  ## ... more steps

  pin('promote_sustainable_development'),  step(implement_environmental_protection_measures),
  step(develop_renewable_energy_sources),

  pin('monitor_and_evaluate'),
  step(establish_global_peace_index),
  step(conduct_regular_peace_assessments),
  route(lambda result: 'analyze_current_global_conflicts' if result['conduct_regular_peace_assessments']['global_peace_score'] < 0.9 else 'maintain_peace'),

  pin('maintain_peace'),
  step(continue_peace_initiatives)
]
```

## plans that make plans

this example [docs/examples/system_two/planer.py](docs/examples/system_two/planer.py) takes it one step further and:

* given a problem
* it follows a plan
* to create a plan
* to solve the problem

this is an interesting area to improve on:
* create functions of runtime created plans
* _safely_ execute them
* create more plans
* and keep researching

but even at its current state it is capable of creating and refining (with a stronger model) plans to provide solid approaches to solve complex problems

the gist is:

```python
def plan_maker(problem: str):
    blueprint = plan([
        step(research_problem),   ## as part of research, goes online to supplement LLM knowledge with fresh results
        step(restate_problem),
        step(divide_problem),
        step(create_plan),

        pin('review'),
        step(review_plan),
        route(lambda result: 'refine' if result['review_plan']['needs_refinement'] else 'end'),

        pin('refine'),
        step(refine_plan),
        route(lambda _: 'review'),

        ## create functions
        ## execute plan
        ## validate go back

        pin('end')
    ])

    default_model = thinker.Ollama(model="llama3:70b")
    stronger_model = thinker.Claude(model="claude-3-5-sonnet-20240620")

    mind_map = {
        "review_plan": stronger_model
    }

    result = thinker.plan(blueprint,
                          llm=default_model,
                          mind_map=mind_map,
                          start_with={"problem": problem})
```

# license

Copyright © 2024 tolitius

Distributed under the Eclipse Public License either version 1.0 or (at
your option) any later version.
