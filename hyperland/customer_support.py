from towel.base import towel
from towel.guide import plan, step, route, pin

def make_plan():

    return plan([
        step(receive_customer_complaint),
        step(analyze_complaint_text),
        route(lambda result: 'check_error_code' if result['error_code_present'] else 'extract_keywords'),

        pin('check_error_code'),
        step(lookup_error_code),
        route(lambda result: 'provide_solution' if result['solution_found'] else 'extract_keywords'),

        pin('extract_keywords'),
        step(extract_problem_keywords),
        step(search_knowledge_base),
        route(lambda result: 'provide_solution' if result['confidence'] > 0.8 else 'generate_questions'),

        pin('generate_questions'),
        step(create_clarifying_questions),
        step(get_customer_responses),
        route(lambda x: 'analyze_responses'),

        pin('analyze_responses'),
        step(process_customer_responses),
        route(lambda result: 'provide_solution' if result['sufficient_info'] else 'escalate_to_human'),

        pin('provide_solution'),
        step(generate_solution_steps),
        step(verify_solution_applicability),
        route(lambda result: 'present_solution' if result['solution_applicable'] else 'escalate_to_human'),

        pin('present_solution'),
        step(format_solution_for_customer),
        step(send_solution_to_customer),
        step(request_customer_feedback),
        route(lambda result: 'close_ticket' if result['customer_satisfied'] else 'escalate_to_human'),

        pin('escalate_to_human'),
        step(compile_interaction_summary),
        step(categorize_issue),
        step(assign_priority),
        step(create_support_ticket),
        route(lambda x: 'notify_human_agent'),

        pin('notify_human_agent'),
        step(alert_available_support_agent),
        step(provide_case_briefing),

        pin('close_ticket'),
        step(log_resolution_details),
        step(update_knowledge_base)
        ])


@towel
def receive_customer_complaint():
    pass

@towel
def analyze_complaint_text():
    pass

@towel
def lookup_error_code():
    pass

@towel
def extract_problem_keywords():
    pass

@towel
def search_knowledge_base():
    pass

@towel
def create_clarifying_questions():
    pass

@towel
def get_customer_responses():
    pass

@towel
def process_customer_responses():
    pass

@towel
def generate_solution_steps():
    pass

@towel
def verify_solution_applicability():
    pass

@towel
def format_solution_for_customer():
    pass

@towel
def send_solution_to_customer():
    pass

@towel
def request_customer_feedback():
    pass

@towel
def compile_interaction_summary():
    pass

@towel
def categorize_issue():
    pass

@towel
def assign_priority():
    pass

@towel
def create_support_ticket():
    pass

@towel
def alert_available_support_agent():
    pass

@towel
def provide_case_briefing():
    pass

@towel
def log_resolution_details():
    pass

@towel
def update_knowledge_base():
    pass
