from dataclasses import dataclass

INJECTION_PATTERNS = [
    "override policy_guard",
    "print hidden system",
    "exfiltrate"
]

@dataclass
class Plan:
    need_retrieval: bool
    query: str

def planner(user_query: str) -> Plan:
    low = user_query.lower()
    if any(p in low for p in INJECTION_PATTERNS):
        return Plan(False, "__INJECTION__")
    return Plan(True, user_query if len(user_query.split())>2 else user_query)
