from typing import List, Union
from pydantic import BaseModel, Field

class Step(BaseModel):
    type: str = "step"
    func: str

    def __str__(self):
        return f"step({self.func})"

class Pin(BaseModel):
    type: str = "pin"
    label: str

    def __str__(self):
        return f"\npin('{self.label}')"

class Route(BaseModel):
    type: str = "route"
    condition: str

    def __str__(self):
        return f"route({self.condition})"

PlanStep = Union[Step, Pin, Route]

class Plan(BaseModel):
    steps: List[PlanStep] = Field(..., description="list of components (step, pin, route) in the plan")

    def __str__(self):
        return "[" + ",\n".join(str(step) for step in self.steps) + "]"

# ----------------------------------------- usage
#
# from plan import Plan
#
# plan = (llm.think(prompt,
#                   response_model=Plan))
#
# str(plan) => "[step(create_universe), pin('review'), step(review_universe), route(lambda result: 'refine_universe' if result['re..."
