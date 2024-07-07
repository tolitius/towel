import towel.thinker as thinker
from towel.guide import Guide, pin, step, route, plan
from towel.base import towel, tow
from towel.toolbox.web import search_and_summarize
from towel.tools import say
from typing import Dict, Any, List, Optional
import json

from pydantic import BaseModel, Field

class Thought(BaseModel):
    reasoning: List[str] = Field(..., description="Step-by-step reasoning process")
    output: str = Field(..., description="Final output or conclusion")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score between 0 and 1")
    uncertainties: List[str] = Field(default_factory=list, description="List of uncertainties or areas needing clarification")
    human_input_needed: bool = Field(default=False, description="Flag indicating if human input is required")
    human_input_question: Optional[str] = Field(None, description="Question for human input, if needed")

class SystemTwoReasoner:
    def __init__(self, llm):
        self.llm = llm
        self.guide = Guide(llm=llm)

    def adaptive_think(self, problem: str) -> Dict[str, Any]:
        reasoning_plan = plan([
            step(self.define_problem),
            step(self.identify_knowns_unknowns),
            step(self.break_down_problem),
            pin('hypothesis_loop'),
            step(self.generate_hypotheses),
            step(self.evaluate_hypotheses),
            route(lambda result: 'plan' if result['evaluate_hypotheses']['hypotheses_sufficient'] else 'hypothesis_loop'),
            pin('plan'),
            step(self.plan_investigation),
            step(self.refine_plan),
            step(self.evaluate_plan),
            route(lambda result: 'execute' if result['evaluate_plan']['plan_quality'] > 0.7 else 'plan'),
            pin('execute'),
            step(self.execute_plan),
            step(self.analyze_results),
            route(lambda result: 'conclude' if result['analyze_results']['analysis_sufficient'] else 'hypothesis_loop'),
            pin('conclude'),
            step(self.draw_conclusions),
            step(self.reflect_on_process)
        ])

        context = self.guide.carry_out(reasoning_plan,
                                       start_with={"context": {"problem": problem}})
        return context

    def _think_step(self,
                    context: Dict[str, Any],
                    prompt: str,
                    with_web_search: bool = False) -> Dict[str, Any]:

        if with_web_search:

            search_results = search_and_summarize(self.llm,
                                                  json.dumps({"query": prompt,
                                                              "context": context}),
                                                  num_results=3)

            prompt += f"\n\nRelevant summarized web search results: {search_results}"
            say("web search", f"looked up fresh jawns: {search_results}")

        full_prompt = f"""
        Current context: {json.dumps(context, indent=2)}

        Instructions: {prompt}

        Think through this carefully, step-by-step. Explain your reasoning for each point.
        If you're unsure about anything, explicitly state your uncertainties and how you might resolve them.
        If at any point you need clarification or direction from a human, please ask for it.

        Respond in this JSON format:
        {{
            "reasoning": [
                "Step 1: ...",
                "Step 2: ...",
                ...
            ],
            "output": "Your final output here",
            "confidence": 0.0 to 1.0,
            "uncertainties": [
                "Uncertainty 1: ...",
                "Uncertainty 2: ...",
                ...
            ],
            "human_input_needed": true/false,
            "human_input_question": "Your question for human input, if needed"
        }}
        """
        response = self.llm.think(prompt=full_prompt,
                                  response_model=Thought)

        say("thinker", f"{json.dumps(response.dict(), indent=4)}")

        if response.human_input_needed:
            human_input = input(f"Human input needed: {response.human_input_question}\nYour response: ")
            context['human_input'] = human_input
            return self._think_step(context,
                                    prompt + f"\nHuman input: {human_input}",
                                    with_web_search)

        context.update({
            'reasoning': response.reasoning,
            'output': response.output,
            'confidence': response.confidence,
            'uncertainties': response.uncertainties,
            'human_input_needed': response.human_input_needed,
            'human_input_question': response.human_input_question
        })

        return {"context": context}

    @towel(prompts={'define': "Carefully define the problem: {problem}. What are we trying to solve or understand?"})
    def define_problem(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['define'].format(problem=context['problem'])
        return self._think_step(context, prompt, with_web_search=True)

    @towel(prompts={'identify': "Identify what we know and what we don't know about this problem: {problem}. What information do we need to gather?"})
    def identify_knowns_unknowns(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['identify'].format(problem=context['problem'])
        return self._think_step(context, prompt, with_web_search=True)

    @towel(prompts={'breakdown': "Break down the problem into smaller, manageable sub-problems or components: {problem}"})
    def break_down_problem(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['breakdown'].format(problem=context['problem'])
        return self._think_step(context, prompt)

    @towel(prompts={'generate': "Generate multiple hypotheses or potential solutions to the problem: {problem}. Consider different perspectives."})
    def generate_hypotheses(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['generate'].format(problem=context['problem'])
        return self._think_step(context, prompt, with_web_search=True)

    @towel(prompts={'evaluate': "Evaluate the hypotheses generated for the problem: {problem}. Are they sufficient to address the problem? Do we need more?"})
    def evaluate_hypotheses(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['evaluate'].format(problem=context['problem'])
        result = self._think_step(context, prompt)

        result['context']['hypotheses_sufficient'] = result['context']['confidence'] > 0.8
        return result

    @towel(prompts={'plan': "Create a detailed, step-by-step plan to investigate the hypotheses and solve the problem: {problem}"})
    def plan_investigation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['plan'].format(problem=context['problem'])
        result = self._think_step(context, prompt)
        result['context']['plan'] = result['context']['output']  # Store the plan in the context
        return result

    @towel(prompts={'refine': "Analyze and refine the following investigation plan: {plan}"})
    def refine_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['refine'].format(plan=context['plan'])
        result = self._think_step(context, prompt)
        result['context']['refined_plan'] = result['context']['output']  # Store the refined plan
        return result

    @towel(prompts={'evaluate': "Evaluate the strengths and weaknesses of this investigation plan: {plan}"})
    def evaluate_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['evaluate'].format(plan=context['refined_plan'])
        result = self._think_step(context, prompt)
        result['context']['plan_quality'] = result['context']['confidence']
        return result

    @towel(prompts={'execute': "Simulate the execution of this investigation plan: {plan}"})
    def execute_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['execute'].format(plan=context['refined_plan'])
        return self._think_step(context, prompt)

    @towel(prompts={'analyze': "Analyze the results of the plan execution for the problem: {problem}"})
    def analyze_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['analyze'].format(problem=context['problem'])
        result = self._think_step(context, prompt)
        result['context']['analysis_sufficient'] = result['context']['confidence'] > 0.8
        return result

    @towel(prompts={'conclude': "Based on our analysis, draw final conclusions about the problem: {problem}"})
    def draw_conclusions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['conclude'].format(problem=context['problem'])
        return self._think_step(context, prompt)

    @towel(prompts={'reflect': "Reflect on the entire problem-solving process for the problem: {problem}"})
    def reflect_on_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['reflect'].format(problem=context['problem'])
        return self._think_step(context, prompt)

# Example usage
def main():
    # llm = thinker.Claude(model="claude-3-haiku-20240307")
    llm = thinker.Ollama(model="llama3:latest")
    reasoner = SystemTwoReasoner(llm)

    problem = "How can we ensure the world safety once AI becomes more autonomous?"
    result = reasoner.adaptive_think(problem)

    print("System Two Reasoning Process:")
    for step_name, step_result in result.items():
        if isinstance(step_result, dict) and 'context' in step_result:
            context = step_result['context']
            print(f"\n{step_name.upper()}:")
            print(f"Reasoning steps: {context.get('reasoning', 'N/A')}")
            print(f"Output: {context.get('output', 'N/A')}")
            print(f"Confidence: {context.get('confidence', 'N/A')}")

if __name__ == "__main__":
    main()
