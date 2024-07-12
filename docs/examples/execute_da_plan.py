import argparse, os
from typing import Any, Dict

from pydantic import BaseModel

from towel import towel, tow, pin, step, route, plan
import towel.thinker as thinker

from towel.tools import color, LogLevel, stream, say, slurp
from towel.guide import Guide

class Review(BaseModel):
    feedback: str
    quality_score: float

@towel(iam="Business Analyst",
        prompts={
            'create': "Given these requirements: {requirements}, create user stories that will be used to implement these requirements."
})
def create_stories(requirements: str) -> Dict[str, Any]:

    llm, prompts, _, iam, _ = tow()
    print(color.GRAY_ME + f"  |>  (using: {llm})" + color.END)

    prompt = prompts['create'].format(requirements=requirements)

    stories = stream(llm.think(prompt=prompt,
                               stream=True),
                     who=iam)

    return {'stories': stories}

@towel(iam="Product Manager",
        prompts={
            'review': """Given the requirements, review the user stories:

## requirements
{requirements}

## user stories
{stories}

## instructions
Provide feedback and a quality score from 0 to 1.

Only give a score higher than 0.7 if ALL of these are true:

 * every story has a well written acceptance criteria in Gherkin format.
 * every story has a well written user story summary.
 * every story has one or more examples.
 * user stories focus on splitting the requirements by distinct implementable features.
 * all the details are concise, complete and clear to implement.

make feedback as detailed as possible

## output format
Return json ONLY in a format of:
{{"quality_score": 0.65,
  "feedback": "focus on splitting these by distinct implementable features"}}
"""
})
def review_stories(stories: str,
                   requirements :str) -> Dict[str, Any]:

    llm, prompts, _, iam, _ = tow()
    print(color.GRAY_ME + f"  |>  (using: {llm})" + color.END)

    prompt = prompts['review'].format(requirements=requirements,
                                      stories=stories)


    review = llm.think(prompt=prompt,
                       response_model=Review)

    say(iam, f"{review}")

    return {"feedback": review.feedback,
            "quality_score": review.quality_score}

@towel(iam="Business Analyst",
        prompts={
            'revise': """Revise these user stories based on the requirements and the feedback:
## requirements
{requirements}

## feedback
{feedback}

## user stories
{stories}"""
})
def revise_stories(stories: str,
                   feedback: str,
                   requirements: str) -> Dict[str, Any]:

    llm, prompts, _, iam, _  = tow()
    print(color.GRAY_ME + f"  |>  (using: {llm})" + color.END)

    prompt = prompts['revise'].format(requirements=requirements,
                                      stories=stories,
                                      feedback=feedback)

    revised = stream(llm.think(prompt=prompt,
                               stream=True),
                     who=iam)

    return {"stories": revised}

@towel(iam="Engineer",
        prompts={
            'implement': "Use Python to implement the requirements described in these user stories: {stories}"
})
def implement_code(stories: str) -> str:

    llm, prompts, _, iam, _ = tow()
    print(color.GRAY_ME + f"  |>  (using: {llm})" + color.END)

    prompt = prompts['implement'].format(stories=stories)

    code = stream(llm.think(prompt=prompt,
                            stream=True),
                  who=iam)

    return code

def make_plan():

    return plan([

        step(create_stories),

        pin('review'),
        step(review_stories),
        route(lambda result: 'revise' if result['review_stories']['quality_score'] < 0.8 else 'implement'),

        pin('revise'),
        step(revise_stories),
        route(lambda x: 'review'),

        pin('implement'),
        step(implement_code)
])

# usage:
# $ poetry run python hyperland/daplan.py

def parse_args():
    parser = argparse.ArgumentParser(description="based on requirements create user stories, review them, revise them, and implement them")
    parser.add_argument("-r", "--requirements", required=False, help="path to a file with requirements")

    args = parser.parse_args()
    requirements = args.requirements

    if requirements is None:
        print(color.YELLOW + f"missing requirements" + color.END + " pass them as \"--requirements path/to/requirements.txt\". would use a simple \"to-do list\" requirements for now")
        args.default_requirements = "create a to-do list app with task prioritization and due dates"

    return args

def main():

    args = parse_args()
    if args.requirements:
        requirements = slurp(args.requirements)
    else:
        requirements = args.default_requirements

    claude = thinker.Claude(model="claude-3-haiku-20240307")
    llama = thinker.Ollama(model="llama3:latest")
                           # url="http://remote-host:11434")

    print(color.GRAY_MEDIUM + f"{claude}" + color.END)
    print(color.GRAY_MEDIUM + f"{llama}" + color.END)

    blueprint = make_plan()

    thinker.plan(blueprint,
                 llm=llama,
                 mind_map={"review_stories": claude},
                 start_with={"requirements": requirements})

    ## ------------- can be also done "manually" as:

    # guide = Guide(llm=llm)
    # user_stories = guide.carry_out(blueprint,
    #                                {"requirements": requirements})

    ## print(color.GRAY_VERY_LIGHT + f"user stories: {user_stories}" + color.END)

if __name__ == '__main__':
    main()
