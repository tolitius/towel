from towel import towel, tow, intel
from towel.type import Plan
from towel.thinker import Ollama, Claude
from towel.prompt import make_plan

@towel(prompts={'plan': """given this problem: {problem} {make_plan}"""})
def make_da_plan(problem: str):
    llm, prompts, *_ = tow()
    plan = llm.think(prompts['plan'].format(problem=problem,
                                            make_plan=make_plan),
                     response_model=Plan)
    return plan



llm = Ollama(model="llama3:70b")
# llm = Claude(model="claude-3-haiku-20240307")

with intel(llm=llm):
    plan = make_da_plan("make sure there are no wars")

print(f"\n{str(plan)}")

# =>> claude says:
#
# [
#   step(analyze_current_global_conflicts),
#   step(identify_root_causes),
#   step(assess_diplomatic_relations),
#   route(lambda result: 'improve_diplomacy' if result['assess_diplomatic_relations']['status'] == 'poor' else 'address_economic_factors'),

#   pin('improve_diplomacy'),
#   step(organize_peace_talks),
#   step(implement_conflict_resolution_strategies),
#   route(lambda result: 'address_economic_factors' if result['implement_conflict_resolution_strategies']['success'] else 'reassess_diplomatic_approach'),

#   pin('reassess_diplomatic_approach'),
#   step(revise_diplomatic_strategies),
#   route(lambda result: 'improve_diplomacy'),

#   pin('address_economic_factors'),
#   step(analyze_economic_inequalities),
#   step(develop_economic_aid_programs),
#   step(implement_fair_trade_policies),

#   pin('enhance_education'),
#   step(improve_global_education_systems),
#   step(promote_cultural_understanding),

#   pin('strengthen_international_organizations'),
#   step(reform_un_security_council),
#   step(enhance_peacekeeping_operations),

#   pin('address_arms_control'),
#   step(negotiate_disarmament_treaties),
#   step(implement_arms_reduction_programs),

#   pin('promote_sustainable_development'),
#   step(implement_environmental_protection_measures),
#   step(develop_renewable_energy_sources),

#   pin('monitor_and_evaluate'),
#   step(establish_global_peace_index),
#   step(conduct_regular_peace_assessments),
#   route(lambda result: 'analyze_current_global_conflicts' if result['conduct_regular_peace_assessments']['global_peace_score'] < 0.9 else 'maintain_peace'),

#   pin('maintain_peace'),
#   step(continue_peace_initiatives)
# ]
