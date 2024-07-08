from towel.base import towel, tow
from towel.guide import Guide, step, route, plan, pin
from towel.thinker import Ollama, Claude
from towel.tools import say
from typing import Dict, Any
import json

@towel(prompts={'summarize': "Summarize this white paper abstract on quantum computing: {abstract}"})
def summarize_abstract(abstract: str) -> Dict[str, Any]:

    llm, prompts, _, iam, _ = tow()
    summary = llm.think(prompts['summarize'].format(abstract=abstract))

    say(iam, f"summary: {json.dumps(summary.content[0].text[:100], indent=4)}...")
    return {"summary": summary.content[0].text}

@towel(prompts={
    'assess': "Assess the feasibility of implementing the quantum computing approach described in this summary: {summary}",
    'score': "Based on your assessment, provide a feasibility score from 1 to 10, where 1 is extremely difficult and 10 is very feasible. Respond with only the numeric score."
})
def assess_feasibility(summary: str) -> Dict[str, Any]:

    llm, prompts, _, iam, _ = tow()
    assessment = llm.think(prompts['assess'].format(summary=summary))

    score_response = llm.think(prompts['score'])
    try:
        feasibility_score = int(score_response.content[0].text.strip())

        feasibility_score = max(1, min(10, feasibility_score))
    except ValueError:
        feasibility_score = 5

    response = {"feasibility": assessment.content[0].text,
                "feasibility_score": feasibility_score}

    say(iam, f"assessment: {response}")
    return response

@towel(prompts={'design_simple': "Design a simplified high-level system architecture for a quantum computer based on this summary: {summary}. Consider the feasibility assessment: {feasibility}"})
def design_simple_architecture(summary: str,
                               feasibility: str) -> Dict[str, Any]:

    llm, prompts, context, *_, iam = tow()
    architecture = llm.think(prompts['design_simple'].format(summary=summary,
                                                             feasibility=feasibility))

    # say(iam, f"architecture: {json.dumps(architecture.content[0].text)[:100]}...")
    return {"architecture": architecture.content[0].text}

@towel(prompts={'design_complex': "Design a comprehensive high-level system architecture for a quantum computer based on this summary: {summary}. Consider the feasibility assessment: {feasibility}"})
def design_complex_architecture(summary: str,
                                feasibility: str) -> Dict[str, Any]:

    llm, prompts, context, *_, iam = tow()
    architecture = llm.think(prompts['design_complex'].format(summary=summary,
                                                              feasibility=feasibility))

    # say(iam, f"architecture: {json.dumps(architecture.content[0].text)[:100]}...")
    return {"architecture": architecture.content[0].text}

@towel(prompts={'plan': "Create an implementation plan for this quantum computing architecture: {architecture}. Refer back to the original abstract: {abstract}"})
def create_implementation_plan(architecture: str,
                               abstract: str) -> Dict[str, Any]:

    llm, prompts, context, *_, iam = tow()
    plan = llm.think(prompts['plan'].format(architecture=architecture,
                                            abstract=abstract))

    # say(iam, f"implementation_plan: {json.dumps(plan.content[0].text)[:100]}...")
    return {"implementation_plan": plan.content[0].text}

def main():

    # llm = Claude(model="claude-3-haiku-20240307")
    llm = Ollama(model="llama3:latest")
    guide = Guide(llm)

    quantum_computing_plan = plan([
        step(summarize_abstract),
        step(assess_feasibility),
        route(lambda result: 'simple' if result['assess_feasibility']['feasibility_score'] <= 5 else 'complex'),

        pin('simple'),
        step(design_simple_architecture),
        route(lambda x: 'plan'),

        pin('complex'),
        step(design_complex_architecture),
        route(lambda x: 'plan'),

        pin('plan'),
        step(create_implementation_plan)
    ])

    # A more realistic quantum computing white paper abstract
    abstract = """
    This white paper presents a novel approach to scaling quantum computers using spin qubits in silicon.
    We propose a scalable architecture that leverages existing semiconductor manufacturing techniques
    to create a dense array of qubits with high fidelity gate operations. Our method involves:
    1) A new qubit design that enhances coherence times
    2) An innovative control scheme for multi-qubit operations
    3) A scalable readout mechanism for large qubit arrays
    Preliminary results show a 10x improvement in qubit fidelity and a 5x increase in coherence times
    compared to current state-of-the-art. This approach paves the way for practical quantum computers
    with thousands of qubits, potentially enabling breakthroughs in cryptography, drug discovery, and
    materials science.
    """

    result = guide.carry_out(quantum_computing_plan,
                             start_with={"abstract": abstract})

    print("\nQuantum Computing White Paper Implementation Analysis:")
    print(f"Summary: {result['summarize_abstract']['summary'][:500]}...")
    print(f"Feasibility Assessment: {result['assess_feasibility']['feasibility'][:500]}...")
    print(f"Architecture Design: {result['design_complex_architecture']['architecture'][:500]}...")
    print(f"Implementation Plan: {result['create_implementation_plan']['implementation_plan'][:500]}...")

if __name__ == "__main__":
    main()
