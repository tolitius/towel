from towel import thinker, towel, tow, intel, plan, step, route, pin
from towel.type import Plan
from towel.prompt import make_plan
from towel.toolbox.web import read_url_as_text

from towel.tools import say, LogLevel, color

from typing import List, Dict, Any

from pydantic import BaseModel, Field
import argparse
import json

## ------------------------------------ read a white paper and summarize its key points

class PaperSummary(BaseModel):
    summary: str = Field(..., description="A concise summary of the paper")
    steps: List[str] = Field(..., description="List of steps used in the paper to implement its ideas")
    key_concepts: List[str] = Field(..., description="List of key concepts from the paper")

@towel(prompts={
    'summarize': """Summarize the key steps in this research paper that are required to implement the proposed solution:

    We would need all the details and steps taken in the paper in order to later make Python functions and implement these ideas
    Hence don't miss important steps and details that should be addressed in the implementation.

    Focus on:
    1. ALL the steps in this paper to implement the solution
    2. The main problem or challenge addressed
    3. The proposed solution or methodology

    White paper content: {content}

    Provide the summary as a JSON object with the following structure:
    {{
        "summary": "A concise but full summary of the paper",
        "key_concepts": ["List", "of", "key", "concepts"],
        "steps": ["List", "of", "steps"]
    }}

    focus on steps this research takes to get to the goal
    when extracting steps be as detailed as possible
    make sure all the steps are very detailed with all the necessary information to later be converted to a Python function
    """
})
def summarize_paper(url: str) -> PaperSummary:

    llm, prompts, *_ = tow()

    paper_content = read_url_as_text(url)

    summary = llm.think(prompts['summarize'].format(content=paper_content),
                        response_model=PaperSummary)

    return {
        **summary.dict(),
        # "research": paper_content,
    }

## ------------------------------------ is it feasible to implement the ideas in this white paper?

class FeasibilityAssessment(BaseModel):
    feasibility_score: float = Field(..., ge=0, le=1, description="Feasibility score between 0 and 1")
    main_challenges: List[str] = Field(..., description="List of main challenges for implementation")
    implementation_complexity: str = Field(..., description="Estimated complexity of implementation")
    resource_requirements: str = Field(..., description="Estimated resource requirements")

@towel(prompts={
    'assess': """Based on the following summary and key concepts of a white paper, assess the technical feasibility of implementing the proposed ideas:

    Summary: {summary}
    Key Concepts: {key_concepts}

    Consider the following aspects:
    1. Technical complexity
    2. Resource requirements (time, computational power, data, expertise)
    3. Current state of technology
    4. Potential roadblocks or challenges

    Provide your assessment as a JSON object with the following structure:
    {{
        "feasibility_score": 0.7,
        "main_challenges": ["Challenge 1", "Challenge 2", "Challenge 3"],
        "implementation_complexity": "A brief description of the implementation complexity",
        "resource_requirements": "A brief description of the required resources"
    }}

    The feasibility score should be between 0 and 1, where 0 is completely infeasible and 1 is easily feasible.
    """
})
def assess_feasibility(summary: str,
                       key_concepts: List[str]) -> dict:

    llm, prompts, *_ = tow()

    assessment = llm.think(prompts['assess'].format(
        summary=summary,
        key_concepts=", ".join(key_concepts)
    ), response_model=FeasibilityAssessment)

    return assessment.dict()

## ------------------------------------ design the technical approach

class PlanFunction(BaseModel):
    name: str = Field(..., description="Name of the function in snake_case")
    purpose: str = Field(..., description="Purpose or responsibility of the function")
    uses_llm: bool = Field(..., description="Whether this function requires an LLM to operate")

class Design(BaseModel):
    overview: str = Field(..., description="High-level overview of the functional architecture")
    functions: List[PlanFunction] = Field(..., description="List of main functions in the architecture")
    execution_flow: str = Field(..., description="Description of the execution flow between functions")

def shape_functions(design: Design) -> Dict[str, Any]:
    shaped_functions = []
    for func in design.functions:
        shaped_function = {
            "name": func.name,
            "purpose": func.purpose,
            "uses_llm": func.uses_llm
        }
        shaped_functions.append(shaped_function)

    return {
        "overview": design.overview,
        "functions": shaped_functions,
        "execution_flow": design.execution_flow
    }

@towel(prompts={
    'design_functions': """Based on the following information, design a list of functions required to implement the solution described in the research paper:

    Summary: {summary}
    Key Concepts: {key_concepts}
    Steps Taken in the Research Paper: {steps}
    Main Challenges: {main_challenges}

    For each function, provide the following information:
    {{
        "name": "function_name_in_snake_case",
        "purpose": "Purpose of this function",
        "uses_llm": true  // or false
    }}

    Ensure that:
    1. Function names are in snake_case and specific to the research paper's implementation.
    2. Each function has a clear purpose related to the paper's steps or challenges.
    3. The 'uses_llm' field is correctly set for each function.

    Provide the list of functions as a JSON array.
    """,
    'create_design': """Using the list of functions provided, create a high-level functional architecture:

    Functions: {functions}

    Your response MUST be a valid JSON object with the following structure:
    {{
        "overview": "A brief overview of the entire functional architecture",
        "functions": unchanged functions from above (as a JSON array),
        "execution_flow": "Description of how the functions are executed and how data flows between them"
    }}

    Ensure that:
    1. The "overview" provides a concise summary of the architecture.
    2. The "functions" field is exactly the same as the input provided.
    3. The "execution_flow" describes how the functions work together to implement the solution.

    Design the architecture to address all key aspects of the paper, including main challenges and novel approaches.
    """
})
def design_architecture(summary: str,
                        key_concepts: List[str],
                        steps: List[str],
                        feasibility_score: float,
                        main_challenges: List[str]) -> dict:
    llm, prompts, *_ = tow()

    # design functions
    flat_functions = llm.think(prompts['design_functions'].format(
        summary=summary,
        key_concepts=", ".join(key_concepts),
        steps=", ".join(steps),
        main_challenges=", ".join(main_challenges)
    ), response_model=List[PlanFunction])

    # create design
    flat_design = llm.think(prompts['create_design'].format(
        functions=json.dumps([func.dict() for func in flat_functions], indent=2)
    ), response_model=Design)

    # shape the functions and create the final design structure
    final_design = shape_functions(flat_design)

    return {"architecture": final_design}

@towel(prompts={
    'make_plan': """Given the research and its architecture:

Summary: {summary}
Key Concepts: {key_concepts}
Research Steps: {steps}
Functional Architecture:
{architecture}

## INSTRUCTIONS:
Create a detailed plan to implement the ideas presented in this research.
Make sure the final plan adheres to the architecture, initial research steps and addresses the main challenges.

Plan steps should not be generic or broad, but instead be VERY specific to the research paper steps and the architecture design.

{make_plan}
"""
})
def make_da_plan(summary: str,
                 key_concepts: List[str],
                 steps: List[str],
                 architecture: Dict[str, Any]) -> Dict[str, Any]:

    llm, prompts, *_ = tow()

    plan = llm.think(prompts['make_plan'].format(
        summary=summary,
        key_concepts=", ".join(key_concepts),
        steps=", ".join(steps),
        architecture=json.dumps(architecture, indent=2),
        make_plan=make_plan
    ), response_model=Plan)

    return plan


## --------------------------- white paper to executable plan

paper_plan = plan([

    step(summarize_paper),
    step(assess_feasibility),
    route(lambda result: 'design' if result['assess_feasibility']['feasibility_score'] > 0.5 else 'end'),

    pin('design'),
    step(design_architecture),
    step(make_da_plan),

    pin('end')
])

## --------------------------- executing a plan

# usage:
# $ poetry run python docs/examples/white_paperer.py -p "https://url/to/whitepaper"

def parse_args():
    parser = argparse.ArgumentParser(description="creates a plan to implement a white paper from a given URL")
    parser.add_argument("-p", "--paper-url", help="white paper url")

    args = parser.parse_args()
    paper_url = args.paper_url

    if paper_url is None:
        ## "Monte Carlo Tree Self-refine"
        args.paper_url = "https://arxiv.org/pdf/2406.07394"

    return args

def main():

    args = parse_args()

    # llm = thinker.Ollama(model="llama3:latest")
    llm = thinker.Claude(model="claude-3-haiku-20240307")
    # llm = thinker.Claude(model="claude-3-5-sonnet-20240620")

    print(color.GRAY_MEDIUM + f"{llm}" + color.END)

    doit = thinker.plan(paper_plan,
                        llm=llm,
                        # log_level=LogLevel.TRACE,
                        start_with={"url": args.paper_url})

    say("summary", f"{json.dumps(doit['summarize_paper'], indent=2)}\n")
    say("planned it:", f"{doit['make_da_plan']}")

if __name__ == "__main__":
    main()
