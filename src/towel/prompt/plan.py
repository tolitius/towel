make_plan = f"""
Create a detailed plan to solve the overall problem. The plan should include steps, pins, and routes.

## Plan Syntax Explanation

A plan is a list of components that define the execution flow of a problem-solving process. It consists of three main components:

1. **Step**: Represents a task to be performed, will execute a function.
   Format: {{"type": "step", "func": "function_name"}}
   - IMPORTANT: `function_name` must be a valid Python function name (lowercase, underscores for spaces)
   - Each step function returns a dictionary, which is automatically passed to subsequent steps
   - Example: {{"type": "step", "func": "design_interface"}}

2. **Pin**: Creates a named point in the plan that can be referenced by routes
   Format: {{"type": "pin", "label": "pin_name"}}
   - IMPORTANT: `pin_name` must be a lowercase string identifier for the pin, with underscores for spaces
   - Example: {{"type": "pin", "label": "requirements_defined"}}

3. **Route**: Directs the flow based on a condition
   Format: {{"type": "route", "condition": "lambda result: condition"}}
   - The lambda function takes a 'result' parameter, which contains all previous step results
   - You can access specific step results using: `result['step_name']['returned_key']`
   - The condition should evaluate to a pin name (as a string) or a boolean
   - Example: {{"type": "route", "condition": "lambda result: 'implement_functionality' if result['define_requirements']['completeness'] > 0.8 else 'revise_requirements'"}}

## Important Notes

- The plan should follow a logical flow to solve the problem
- Ensure that all necessary steps are included and properly connected with routes and pins
- Function names in steps must be lowercase with underscores for spaces
- Pin labels must be lowercase with underscores for spaces
- Routes must use lambda functions and correct result access syntax

## Example of a correctly formatted plan for the given problem

```python
[
    {{"type": "step", "func": "analyze_white_paper"}},
    {{"type": "step", "func": "assess_feasibility"}},
    {{"type": "route", "condition": "lambda result: 'conduct_research' if result['assess_feasibility']['score'] > 0.7 else 'seek_expert_input'"}},
    {{"type": "pin", "label": "seek_expert_input"}},
    {{"type": "step", "func": "consult_expert"}},
    {{"type": "route", "condition": "lambda result: 'conduct_research' if result['consult_expert']['proceed'] else 'end_research'"}},
    {{"type": "pin", "label": "conduct_research"}},
    {{"type": "step", "func": "perform_experiment"}},
    {{"type": "route", "condition": "lambda result: 'compile_findings' if result['perform_experiment']['success'] else 'revise_approach'"}},
    {{"type": "pin", "label": "revise_approach"}},
    {{"type": "step", "func": "modify_research_design"}},
    {{"type": "route", "condition": "lambda result: 'conduct_research'"}},
    {{"type": "pin", "label": "compile_findings"}},
    {{"type": "step", "func": "write_research_paper"}},
    {{"type": "pin", "label": "end_research"}}
]
```

When creating a plan, ensure that it follows this structure and includes all necessary steps to solve the given problem. Remember to use lowercase function names with underscores, proper pin labels, and correctly formatted lambda functions in routes.
"""
