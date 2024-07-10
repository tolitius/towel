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

    def _think_step(self,
                    problem: str,
                    prompt: str,
                    context: Dict[str, Any] = None,
                    with_web_search: bool = False) -> Dict[str, Any]:
        full_prompt = f"""
        Current problem: {problem}
        Context: {json.dumps(context, indent=2) if context else "No additional context"}

        Instructions: {prompt}

        Think through this carefully, step-by-step. Explain your reasoning for each point.
        If you're unsure about anything, explicitly state your uncertainties and how you might resolve them.
        If you need to ask for human direction, ask for it, but make sure your question is:
          - very specific
          - a direction you need from human to complete this ask
          - not a general question
        Do not ask for human input unless you can't research it yourself.
        Do not ask for human input unless absolutely necessary.
        """

        if with_web_search:
            search_results = search_and_summarize(
                self.llm,
                json.dumps({"query": prompt, "problem": problem, "context": context}),
                num_results=3
            )
            full_prompt += f"\nRelevant summarized web search results: {search_results}"
            say("web search", f"looked up fresh information: {search_results}")

        full_prompt += """
        Respond in this JSON format:
        {
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
        }
        """
        response = self.llm.think(
            prompt=full_prompt,
            response_model=Thought
        )

        say("thinker", f"{json.dumps(response.dict(), indent=4)}")

        if response.human_input_needed:
            human_input = input(f"Human input needed: {response.human_input_question}\nYour response: ")
            return self._think_step(
                problem,
                prompt + f"\nHuman input: {human_input}",
                context=context,
                with_web_search=with_web_search
            )

        return response.dict()

    @towel(prompts={'define': "Carefully define the problem of this topic: {topic}. What are we trying to solve or understand?"})
    def define_problem(self,
                       topic: str) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['define'].format(topic=topic)
        thought = self._think_step(
            topic,
            prompt,
            with_web_search=True
        )
        return {"topic": topic,
                "problem": thought}

    @towel(prompts={'identify': "Identify what we know and what we don't know about this problem: {problem}. What information do we need to gather?"})
    def identify_knowns_unknowns(self,
                                 topic: str,
                                 problem: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['identify'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=topic,
            with_web_search=True
        )
        return {"knowns_unknowns": thought}

    @towel(prompts={'breakdown': "Break down the problem into smaller, manageable sub-problems or components: {problem}"})
    def break_down_problem(self,
                           problem: str,
                           knowns_unknowns: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['breakdown'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context={"problem": problem,
                     "knowns_unknowns": knowns_unknowns}
        )
        return {"problem_breakdown": thought}

    @towel(prompts={'generate': "Generate multiple hypotheses or potential solutions to the problem: {problem}. Consider different perspectives."})
    def generate_hypotheses(self,
                            problem: str,
                            problem_breakdown: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['generate'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=problem_breakdown,
            with_web_search=True
        )
        return {"hypotheses": thought}

    @towel(prompts={'evaluate': "Evaluate the hypotheses generated for the problem: {problem}. Are they sufficient to address the problem? Do we need more?"})
    def evaluate_hypotheses(self,
                            problem: str,
                            hypotheses: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['evaluate'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=hypotheses
        )
        hypotheses_sufficient = thought['confidence'] > 0.8
        return {"hypotheses_evaluation": thought,
                "hypotheses_sufficient": hypotheses_sufficient}

    @towel(prompts={'plan': "Create a detailed, step-by-step plan to investigate the hypotheses and solve the problem: {problem}"})
    def plan_investigation(self,
                           problem: str,
                           hypotheses_evaluation: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['plan'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=hypotheses_evaluation
        )
        thought['plan'] = thought['output']
        return {"investigation_plan": thought}

    @towel(prompts={'refine': "Analyze and refine the following investigation plan: {plan}"})
    def refine_plan(self,
                    problem: str,
                    investigation_plan: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['refine'].format(plan=investigation_plan['plan'])
        thought = self._think_step(
            problem,
            prompt,
            context=investigation_plan
        )
        thought['refined_plan'] = thought['output']
        return {"refined_plan": thought}

    @towel(prompts={'evaluate': "Evaluate the strengths and weaknesses of this investigation plan: {plan}"})
    def evaluate_plan(self,
                      problem: str,
                      refined_plan: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['evaluate'].format(plan=refined_plan['refined_plan'])
        thought = self._think_step(
            problem,
            prompt,
            context=refined_plan
        )
        plan_quality = thought['confidence']
        return {"plan_evaluation": thought,
                "plan_quality": plan_quality}

    @towel(prompts={'execute': "Simulate the execution of this investigation plan: {plan}"})
    def execute_plan(self,
                     problem: str,
                     refined_plan: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['execute'].format(plan=refined_plan['refined_plan'])
        thought = self._think_step(
            problem,
            prompt,
            context=refined_plan
        )
        return {"plan_execution": thought}

    @towel(prompts={'analyze': "Analyze the results of the plan execution for the problem: {problem}"})
    def analyze_results(self,
                        problem: str,
                        plan_execution: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['analyze'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=plan_execution
        )
        analysis_sufficient = thought['confidence'] > 0.8
        return {"results_analysis": thought,
                "analysis_sufficient": analysis_sufficient}

    @towel(prompts={'conclude': "Based on our analysis, draw final conclusions about the problem: {problem}"})
    def draw_conclusions(self,
                         problem: str,
                         results_analysis: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['conclude'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=results_analysis
        )
        return {"conclusions": thought}

    @towel(prompts={'reflect': "Reflect on the entire problem-solving process for the problem: {problem}"})
    def reflect_on_process(self,
                           problem: str,
                           conclusions: Dict[str, Any]) -> Dict[str, Any]:
        llm, prompts, *_ = tow()
        prompt = prompts['reflect'].format(problem=problem)
        thought = self._think_step(
            problem,
            prompt,
            context=conclusions
        )
        return {"reflection": thought}

    def adaptive_think(self, topic: str) -> Dict[str, Any]:

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

        return self.guide.carry_out(
                reasoning_plan,
                start_with={"topic": topic}
                )


def main():
    llm = thinker.Ollama(model="llama3:latest")
    # llm = thinker.Claude(model="claude-3-haiku-20240307")
    reasoner = SystemTwoReasoner(llm)

    topic = "AI will be soon writing _all_ the software, what should kids learn today to be ready for the future?"
    result = reasoner.adaptive_think(topic)

    say("system two", f"{json.dumps(result, indent=4)}")

    print("System Two Reasoning Process:")
    for step_name, step_result in result.items():
        print(f"\n{step_name.upper()}:")
        if isinstance(step_result, dict):
            for key, value in step_result.items():
                if isinstance(value, dict) and 'reasoning' in value:
                    print(f"  {key}:")
                    print(f"    Reasoning steps: {value['reasoning']}")
                    print(f"    Output: {value['output']}")
                    print(f"    Confidence: {value['confidence']}")
                    if 'uncertainties' in value and value['uncertainties']:
                        print(f"    Uncertainties: {value['uncertainties']}")
                    if 'human_input_needed' in value and value['human_input_needed']:
                        print(f"    Human input needed: {value['human_input_question']}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"  {step_result}")

if __name__ == "__main__":
    main()
