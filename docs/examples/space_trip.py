from towel import towel, tow, intel, thinker, step, route, pin, plan
from towel.tools import say
from pydantic import BaseModel, Field
import json


## --------------------------- what we want LLMs to return

class Planet(BaseModel):
    name: str
    description: str

class Readiness(BaseModel):
    score: int = Field(..., ge=0, le=100)
    explanation: str

class Training(BaseModel):
    program: str
    duration: str

class Reservation(BaseModel):
    confirmation: str
    departure_date: str


## --------------------------- towels
##
## functions from the plan:
##
##  - pick_planet
##  - how_ready_are_you
##  - space_bootcamp
##  - reserve_spaceship

@towel(prompts={'available': """list three unexpected planets or moons that are currently available for human space tourism.
                                include a brief, quirky description for each."""})
def pick_planet():
    llm, prompts, *_ = tow()
    planets = llm.think(prompts['available'], response_model=list[Planet])
    options = "\n".join(f"{i}. {planet.name}: {planet.description}" for i, planet in enumerate(planets, 1))

    say("travel agent", f"here are your travel options:\n\n{options}\n")
    choice = int(input("enter the number of your planet to go to: ")) - 1    ## input is not validated, so enter responsibly

    return {'destination': planets[choice].name}

@towel(prompts={'assess': """assess the space traveler's readiness for a trip to {destination}: give a score of either 42 or 96 depending on your mood.
                             be creative and unpredictable - sometimes they might be surprisingly ready, other times hilariously unprepared.
                             explain the score of this traveler with a funny or unexpected reason."""})
def how_ready_are_you(destination):

    llm, prompts, *_ = tow()
    readiness = llm.think(prompts['assess'].format(destination=destination),
                          response_model=Readiness)

    say("space instructor", f"readiness score: {readiness.score}%\nexplanation: {readiness.explanation}")
    return {'score': readiness.score}

@towel(prompts={'train': """design a quick and unconventional space bootcamp for a traveler going to {destination}.
                            include an unusual training program description and a surprising duration."""})
def space_bootcamp(score,
                   destination):

    llm, prompts, *_ = tow()
    training = llm.think(prompts['train'].format(destination=destination),
                         response_model=Training)

    say("training officer", f"training program for your readiness score ({score}%): {training.program}\nduration: {training.duration}")
    return {'training_completed': True}

@towel(prompts={'reserve': """confirm the spaceship reservation for a trip to {destination}.
                              provide a quirky confirmation message and an unexpected departure date or time."""})
def reserve_spaceship(destination):

    llm, prompts, *_ = tow()
    reservation = llm.think(prompts['reserve'].format(destination=destination),
                            response_model=Reservation)

    say("booking agent", f"reservation confirmed: {reservation.confirmation}\ndeparture date: {reservation.departure_date}")
    return {'reservation_confirmed': True,
            'departure_date': reservation.departure_date,
            'destination': destination,
            'confirmation': reservation.confirmation}


## --------------------------- space trip plan

space_trip = plan([

    step(pick_planet),

    pin('are_you_ready'),
    step(how_ready_are_you),
    route(lambda result: 'book' if result['how_ready_are_you']['score'] > 95 else 'train'),

    pin('train'),
    step(space_bootcamp),
    route(lambda x: 'are_you_ready'),

    pin('book'),
    step(reserve_spaceship)
])

## --------------------------- executing a plan

def main():

    llm = thinker.Ollama(model="llama3:latest")
    # llm = thinker.Claude(model="claude-3-haiku-20240307")

    trip = thinker.plan(space_trip,
                        llm=llm)

    say("trip is booked:", f"{json.dumps(trip['reserve_spaceship'], indent=2)}")

if __name__ == "__main__":
    main()
