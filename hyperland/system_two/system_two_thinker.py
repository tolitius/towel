from towel.base import towel, tow
from towel.guide import Guide, step, route, plan, pin
from towel.thinker import Ollama, Claude
from towel.tools import say, color
from towel.toolbox.web import search_web
from typing import Dict, Any, List, Callable
import json

class SystemTwoThinker:
    def __init__(self, llm=None):
        self.llm = llm or Ollama(model="llama3:latest")
        self.guide = Guide(self.llm)

    @towel(prompts={'analyze': "Analyze this problem and create a step-by-step plan to solve it: {problem}"})
    def analyze_problem(self, problem: str) -> Dict[str, Any]:
        llm, prompts, _, iam, _ = tow()
        analysis = llm.think(prompts['analyze'].format(problem=problem))
        return {"steps": json.loads(analysis.content[0].text)}

    @towel(prompts={'generate_function': "Create a Python function to perform this step: {step}"})
    def generate_step_function(self, step: str) -> Dict[str, Any]:
        llm, prompts, _, iam, _ = tow()
        function_code = llm.think(prompts['generate_function'].format(step=step))
        return {"function": function_code.content[0].text}

    def execute_step(self, function_code: str, context: Dict[str, Any]) -> Any:
        # This function would safely execute the generated code
        # It needs proper implementation with security measures
        local_vars = {**context, 'search_web': search_web}
        exec(function_code, local_vars)
        return local_vars.get('result', None)

    @towel(prompts={'human_input': "Request human input for this step: {step}"})
    def request_human_input(self, step: str) -> Dict[str, Any]:
        llm, prompts, _, iam, _ = tow()
        prompt = llm.think(prompts['human_input'].format(step=step))
        user_input = input(f"{prompt.content[0].text}\nYour input: ")
        return {"human_input": user_input}

    def solve(self, problem: str) -> Any:
        def create_step_executor(step: Dict[str, Any]) -> Callable:
            if step['type'] == 'code':
                function = self.generate_step_function(step['description'])['function']
                return lambda context: self.execute_step(function, context)
            elif step['type'] == 'human_input':
                return lambda context: self.request_human_input(step['description'])['human_input']
            else:
                raise ValueError(f"Unknown step type: {step['type']}")

        solution_plan = plan([
            step(self.analyze_problem),
            step(lambda result: {'executors': [create_step_executor(step) for step in result['analyze_problem']['steps']]}),
            step(lambda result: {'solution':
                (lambda executors:
                    (lambda x: x[-1])(
                        [executor({'previous_result': previous_result, 'problem': problem})
                         for executor, previous_result in
                         zip(executors, [None] + [executors[i]({'previous_result': None, 'problem': problem}) for i in range(len(executors)-1)])]))
                (result['executors'])
            })
        ])

        result = self.guide.carry_out(solution_plan, start_with={"problem": problem})
        return result['solution']

# Usage
thinker = SystemTwoThinker()
problem = "What were the top 3 AI breakthroughs in the last year, and how might they impact software development?"
solution = thinker.solve(problem)
print(f"Solution: {solution}")
