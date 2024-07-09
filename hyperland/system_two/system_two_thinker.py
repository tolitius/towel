import subprocess
from typing import Dict, Any, List
from pydantic import BaseModel
from towel import towel, tow, intel
from towel.type import Plan
from towel.thinker import Ollama, Claude
from towel.prompt import make_plan
from towel.toolbox.web import search_and_summarize
from towel.tools import LogLevel
from towel.guide import Guide, step, route, plan, pin

## _in progress_

class SubProblems(BaseModel):
    sub_problems: List[str]

class ReviewResult(BaseModel):
    needs_refinement: bool
    feedback: str

class EvaluationResult(BaseModel):
    needs_improvement: bool
    evaluation: str

@towel(prompts={
    'divide': """Given this problem: {problem}

Divide it into smaller, manageable sub-problems. List these sub-problems in order of priority."""
})
def divide_and_conquer(problem: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    sub_problems = llm.think(prompts['divide'].format(problem=problem), response_model=SubProblems)
    return {"sub_problems": sub_problems.sub_problems}

@towel(prompts={
    'plan': """Create a detailed plan to solve this problem: {problem}

Consider these sub-problems that have been identified:
{sub_problems}

Use the following format for the plan:
{make_plan}

Ensure that your plan addresses the original problem and incorporates solutions for the identified sub-problems."""
})
def make_da_plan(problem: str, sub_problems: List[str]) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    new_plan = llm.think(prompts['plan'].format(
        problem=problem,
        sub_problems="\n".join(f"- {sp}" for sp in sub_problems),
        make_plan=make_plan
    ), response_model=Plan)
    return {"plan": str(new_plan)}

@towel(prompts={
    'review': """Review the following plan:

{plan}

Is this plan sufficient to solve the problem: {problem}?
If not, what improvements are needed?

Return your response as a JSON object:
{{
    "needs_refinement": true/false,
    "feedback": "Your detailed feedback here"
}}""",
    'web_search': """Based on the current plan and problem, what specific information do we need to search for to improve our understanding or approach?"""
})
def review(plan: Plan, problem: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()

    # Determine if web search is needed
    search_query = llm.think(prompts['web_search'].format(plan=plan, problem=problem)).content[0].text
    if search_query:
        search_results = search_and_summarize(llm, search_query)
        print(f"Web search results: {search_results}")
    else:
        search_results = ""

    review = llm.think(prompts['review'].format(plan=plan, problem=problem, search_results=search_results), response_model=ReviewResult)

    if review.needs_refinement:
        print("Review suggests refinement. Feedback:", review.feedback)
        user_input = input("Do you want to provide additional feedback? (yes/no): ").lower()
        if user_input == 'yes':
            human_feedback = input("Please provide your feedback: ")
            review.feedback += f"\nHuman feedback: {human_feedback}"

    return {"needs_refinement": review.needs_refinement, "feedback": review.feedback}

@towel(prompts={
    'refine': """Given the following feedback: {feedback}

Refine this plan:

{plan}

Provide an improved plan using the same format as the original.
{make_plan}"""
})
def make_better_plan(plan: Plan, feedback: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    refined_plan = llm.think(prompts['refine'].format(feedback=feedback, plan=plan, make_plan=make_plan), response_model=Plan)
    return {"plan": str(refined_plan)}

@towel(prompts={
    'create_function': """Create a Python function for the following step in our plan:

Step: {step}

The function should be named '{func_name}' and take any necessary parameters. Include type hints and a docstring explaining the function's purpose and parameters.

Return the function as a string, ready to be executed."""
})
def create_functions(plan: Plan) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    functions = []
    for step in plan.steps:
        if step.type == "step":
            function_str = llm.think(prompts['create_function'].format(step=step, func_name=step.func)).content[0].text
            functions.append(function_str)

    # Combine all functions into a single Python script
    full_script = "\n\n".join(functions)
    return {"functions": full_script}

@towel(prompts={
    'create_main': """Create a Python main function that executes the plan to solve the problem: {problem}

Plan:
{plan}

The main function should call the necessary functions in the correct order to implement the plan.
Include error handling and logging to track the execution process.

Return the main function as a string, ready to be added to our Python script."""
})
def create_main_function(plan: Plan, problem: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    main_function = llm.think(prompts['create_main'].format(problem=problem, plan=plan)).content[0].text
    return {"main_function": main_function}

def execute_plan(functions: str, main_function: str) -> Dict[str, Any]:
    # Combine functions and main function into a single script
    full_script = f"{functions}\n\n{main_function}\n\nif __name__ == '__main__':\n    main()"

    # Write the script to a temporary file
    with open('temp_script.py', 'w') as f:
        f.write(full_script)

    # Execute the script and capture output
    try:
        result = subprocess.run(['python', 'temp_script.py'], capture_output=True, text=True, check=True)
        output = result.stdout
        return {"execution_results": output, "error": None}
    except subprocess.CalledProcessError as e:
        return {"execution_results": None, "error": e.stderr}

@towel(prompts={
    'evaluate': """Evaluate the results of executing this plan:

Execution Output:
{results}

Error (if any):
{error}

Did it successfully solve the problem: {problem}?
Are there any areas that need improvement?

Return your response as a JSON object:
{{
    "needs_improvement": true/false,
    "evaluation": "Your detailed evaluation here"
}}"""
})
def evaluate_results(results: str, error: str, problem: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    evaluation = llm.think(prompts['evaluate'].format(results=results, error=error, problem=problem), response_model=EvaluationResult)
    return {"needs_improvement": evaluation.needs_improvement, "evaluation": evaluation.evaluation}

@towel(prompts={
    'fix_errors': """The following error occurred when executing the plan:

{error}

Please provide fixes for this error. Return your response as a Python code snippet that can be integrated into the existing script to resolve the issue."""
})
def fix_execution_errors(error: str) -> Dict[str, Any]:
    llm, prompts, *_ = tow()
    fixes = llm.think(prompts['fix_errors'].format(error=error)).content[0].text
    return {"fixes": fixes}

def solve_problem(problem: str):
    llm = Ollama(model="llama3:70b")
    # llm = Claude(model="claude-3-haiku-20240307")

    blueprint = plan([
        step(divide_and_conquer),
        step(make_da_plan),

        pin('review'),
        step(review),
        route(lambda result: 'refine_plan' if result['review']['needs_refinement'] else 'create_functions'),

        pin('refine_plan'),
        step(make_better_plan),
        route(lambda _: 'review'),

        pin('create_functions'),
        step(create_functions),
        step(create_main_function),

        pin('execute'),
        step(execute_plan),
        step(evaluate_results),
        route(lambda result: 'fix_errors' if result['evaluate_results']['needs_improvement'] else 'end'),

        pin('fix_errors'),
        step(fix_execution_errors),
        route(lambda _: 'execute'),

        pin('end')
    ])

    guide = Guide(llm,
                  log_level=LogLevel.TRACE)

    with intel(llm=llm):
        final_result = guide.carry_out(blueprint, start_with={"problem": problem})

    return final_result

# Usage
result = solve_problem("make sure there are no wars")
print(f"Final Result: {result}")

# The final plan and functions can be saved to a file like this:
# with open('energy_plan.py', 'w') as f:
#     f.write(result['create_functions']['functions'] + '\n\n' + result['create_main_function']['main_function'])
