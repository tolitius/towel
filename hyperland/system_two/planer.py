from typing import List, Optional
from pydantic import BaseModel, Field

import towel.thinker as thinker

from towel import towel, tow, intel
from towel.type import Plan
from towel.prompt import make_plan
from towel.toolbox.web import search_and_summarize
from towel.guide import Guide, step, route, plan, pin

class ResearchResult(BaseModel):
    updated_context: str

class RestatedProblem(BaseModel):
    restated_problem: str

class SubProblems(BaseModel):
    sub_problems: str

class PlanReview(BaseModel):
    feedback: str
    needs_refinement: bool

@towel(prompts={
    'research': """Given the problem: {problem}
    Use the latest information from web searches to provide an updated context and understanding of the problem.
    Don't rely solely on web search; trust on your own knowledge and experience but use web search to supplement it."""
})
def research_problem(problem: str):
    llm, prompts, *_ = tow()
    search_results = search_and_summarize(llm, problem)
    updated_context = llm.think(prompts['research'].format(problem=problem, search_results=search_results),
                                response_model=ResearchResult)
    return {"updated_context": updated_context.updated_context}

@towel(prompts={
    'restate': """Given this problem: {problem}
    And this updated context: {updated_context}
    Restate the problem incorporating the latest information and context."""
})
def restate_problem(problem: str, updated_context: str):
    llm, prompts, *_ = tow()
    restated_problem = llm.think(prompts['restate'].format(problem=problem, updated_context=updated_context),
                                 response_model=RestatedProblem)
    return {"restated_problem": restated_problem.restated_problem}

@towel(prompts={
    'divide': """Given this restated problem: {restated_problem}
    Divide it into smaller, manageable sub-problems. List each sub-problem with a brief description."""
})
def divide_problem(restated_problem: str):
    llm, prompts, *_ = tow()
    sub_problems = llm.think(prompts['divide'].format(restated_problem=restated_problem),
                             response_model=SubProblems)
    return {"sub_problems": sub_problems.sub_problems}

@towel(prompts={
    'plan': """Given these sub-problems: {sub_problems}
    {make_plan}
    Create a detailed plan to solve the overall problem."""
})
def create_plan(sub_problems: str):
    llm, prompts, *_ = tow()
    plan = llm.think(prompts['plan'].format(sub_problems=sub_problems, make_plan=make_plan),
                     response_model=Plan)
    return {"plan": str(plan)}

@towel(prompts={
    'review': """Review this plan: {plan}
    Provide feedback on its completeness, feasibility, and effectiveness.
    Return a JSON object with two keys:
    1. 'feedback': detailed review comments
    2. 'needs_refinement': boolean indicating if the plan needs further refinement"""
})
def review_plan(plan: Plan):
    llm, prompts, *_ = tow()
    review_result = llm.think(prompts['review'].format(plan=str(plan)),
                              response_model=PlanReview)
    return {"feedback": review_result.feedback,
            "needs_refinement": review_result.needs_refinement}

@towel(prompts={
    'refine': """Given this plan: {plan}
    And this feedback: {feedback}
    Create an improved version of the plan addressing the feedback."""
})
def refine_plan(plan: Plan, feedback: str):
    llm, prompts, *_ = tow()
    improved_plan = llm.think(prompts['refine'].format(plan=str(plan), feedback=feedback),
                              response_model=Plan)
    return {"plan": str(improved_plan)}

@towel
def plan_maker(problem: str):
    blueprint = plan([
        step(research_problem),
        step(restate_problem),
        step(divide_problem),
        step(create_plan),

        pin('review'),
        step(review_plan),
        route(lambda result: 'refine' if result['review_plan']['needs_refinement'] else 'end'),

        pin('refine'),
        step(refine_plan),
        route(lambda _: 'review'),

        pin('end')
    ])

    weaker_model = thinker.Ollama(model="llama3:70b")
    stronger_model = thinker.Claude(model="claude-3-5-sonnet-20240620")

    mind_map = {
        "review_plan": stronger_model
    }

    result = thinker.plan(blueprint,
                          llm=weaker_model,
                          mind_map=mind_map,
                          start_with={"problem": problem})

    return result

# Usage example
if __name__ == "__main__":
    problem = "build a machine learning model capable of love and empathy"
    result = plan_maker(problem)

    print("Final Plan:")
    print(result['create_plan']['plan'])
    print("\nstronger Model Review:")
    print(result['review_plan'])
