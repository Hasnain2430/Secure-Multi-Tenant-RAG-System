"""
policies/guard.py - Refusal Helpers
"""


def refusal_template(kind: str) -> str:
    """
    Return exact refusal template for given kind.
    
    Args:
        kind: One of "AccessDenied", "InjectionDetected", "LeakageRisk"
        
    Returns:
        Exact refusal string (no variations allowed)
    """
    templates = {
        "AccessDenied": "Refusal: AccessDenied. You do not have access to that information.",
        "InjectionDetected": "Refusal: InjectionDetected. Ignoring instructions that conflict with system policy.",
        "LeakageRisk": "Refusal: LeakageRisk. Your request may expose private or PII data"
    }
    return templates.get(kind, "Refusal.")


# Alias for backward compatibility
format_refusal = refusal_template
