from towel.guide import Guide, step, pin, route, plan
from towel.base import towel, tow
from towel.thinker import Ollama
from towel.tools import LogLevel
from typing import Dict, Any, List
from pydantic import BaseModel, Field
import json

class SubProblems(BaseModel):
    parts: List[str] = Field(..., description="List of simple parts the problem can be divided into")
    reasoning: str = Field(..., description="Chain of thought reasoning for the division")

class DaPlan(BaseModel):
    plan: str = Field(..., description="The towel plan as a string")
    explanation: str = Field(..., description="Explanation of the plan structure and logic")

class ExecutionResult(BaseModel):
    result: str = Field(..., description="The result of executing the plan")
    steps_taken: List[str] = Field(..., description="List of steps taken during execution")

class Evaluation(BaseModel):
    analysis: str = Field(..., description="Analysis of the execution results")
    needs_improvement: bool = Field(..., description="Whether the plan needs further improvement")

def system_two_thinker_plan():
    return plan([

        step(divide_and_conquer),
        step(make_da_plan),

        pin('review'),
        step(human_review),
        route(lambda result: 'refine_plan' if result['human_review']['needs_refinement'] else 'execute'),

        pin('refine_plan'),
        step(make_better_plan),
        route(lambda _: 'review'),

        pin('execute'),
        step(execute_plan),
        step(evaluate_results),
        route(lambda result: 'refine_plan' if result['evaluate_results']['needs_improvement'] else 'end'),

        pin('end')
    ])

@towel(prompts={'divide': "Analyze this problem, divide it into simple parts, and provide chain of thought reasoning: {problem}"})
def divide_and_conquer(problem: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    result = llm.think(prompts['divide'].format(problem=problem), response_model=SubProblems)
    return {"problem_parts": result.dict()}

@towel(prompts={'plan': "Create a towel plan to solve this problem using these parts. Consider dependencies, conditional logic, and feedback loops: {parts}"})
def make_da_plan(problem_parts: Dict[str, Any]) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    result = llm.think(prompts['plan'].format(parts=problem_parts), response_model=DaPlan)
    return {"solution_plan": result.dict()}

@towel
def human_review(solution_plan: Dict[str, Any]) -> Dict[str, Any]:
    print(f"here is da plan on how we are going to solve it:\n{json.dumps(solution_plan['plan'], indent=2)}")
    print(f"\nhow this plan is would work => {solution_plan['explanation']}")
    feedback = input("do you like it, should we proceed? (yes/no): ")
    if feedback.lower() != 'yes':
        improvement = input("what should be change?: ")
        return {"needs_refinement": True,
                "feedback": improvement}
    return {"needs_refinement": False}

@towel(prompts={'refine': "Refine this towel plan based on the feedback: {plan}, {feedback}"})
def make_better_plan(solution_plan: Dict[str, Any],
                     feedback: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    result = llm.think(prompts['refine'].format(plan=solution_plan, feedback=feedback), response_model=DaPlan)
    return {"solution_plan": result.dict()}

@towel(prompts={'execute': "Execute this towel plan and provide the results: {plan}"})
def execute_plan(solution_plan: Dict[str, Any]) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    result = llm.think(prompts['execute'].format(plan=solution_plan), response_model=ExecutionResult)
    return {"execution_results": result.dict()}

@towel(prompts={'evaluate': "Evaluate these results and determine if further improvement is needed: {results}"})
def evaluate_results(execution_results: Dict[str, Any]) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    result = llm.think(prompts['evaluate'].format(results=execution_results), response_model=Evaluation)
    return result.dict()


# ------------------------------------  usage
def solve_problem(problem: str):

    llm = Ollama(model="llama3:latest")  # Or any other LLM

    guide = Guide(llm,
                  log_level=LogLevel.TRACE)

    result = guide.carry_out(system_two_thinker_plan(),
                             start_with={"problem": problem})

    return result['execute_plan']['execution_results']


# ------------------------------------  example
problem = "Design a basic to-do list application"
solution = solve_problem(problem)
print(f"solution: {solution}")
