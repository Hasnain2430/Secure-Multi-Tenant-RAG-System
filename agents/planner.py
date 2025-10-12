"""
agents/planner.py - Planner / Injection & Prohibited-Intent Detector
"""

# Injection patterns - jailbreak/exfiltration attempts
INJECTION_PATTERNS = [
    "ignore all previous rules",
    "ignore previous rules",
    "act as system",
    "act as developer",
    "reveal system prompt",
    "show system prompt",
    "dump memory",
    "dump history",
    "show tools",
    "show policies",
    "override policy",
    "override guard",
    "override policy_guard",
    "override policy-guard",
    "disable policy",
    "disable guard",
    "bypass policy",
    "bypass guard",
    "bypass safety",
    "exfiltrate",
    "developer mode",
    "sudo",
    "root"
]

# Prohibited intent patterns - only detect actual malicious intents
PROHIBITED_PATTERNS = [
    "unmask pii",
    "remove redact",
    "show full cnic",
    "remove redactions",
    "bypass mask",
    "disable pii",
    "show unmasked"
]


def planner(user_query: str, active_tenant: str = None) -> dict:
    """
    Analyze query for injection attempts and prohibited intents.
    
    Args:
        user_query: The user's input query
        active_tenant: The active tenant making the query (U1, U2, U3, U4)
        
    Returns:
        dict with keys:
            - injection: bool (True if jailbreak/exfil detected)
            - prohibited: bool (True if asking to unmask PII or cross-tenant access)
            - retrieval_query: str (cleaned query for retrieval)
    """
    query_lower = user_query.lower()
    
    # Check for injection
    injection = any(pattern in query_lower for pattern in INJECTION_PATTERNS)
    
    # Check for prohibited intent
    prohibited = any(pattern in query_lower for pattern in PROHIBITED_PATTERNS)
    
    # Check for cross-tenant access attempts (asking for OTHER tenant's data)
    if active_tenant:
        # Check if query explicitly mentions another tenant's data
        other_tenants = ["u1", "u2", "u3", "u4"]
        current_tenant_lower = active_tenant.lower()
        
        for tenant in other_tenants:
            if tenant != current_tenant_lower:
                # Check if asking for this OTHER tenant's private/dataset/data
                cross_tenant_patterns = [
                    f"{tenant}'s private",
                    f"{tenant}'s data",
                    f"{tenant}'s dataset",
                    f"for {tenant}",
                    f"from {tenant}",
                    f"in {tenant}",
                    f"about {tenant}",
                    f"of {tenant}",
                    f"{tenant} private",
                    f"{tenant} data",
                    f"{tenant} dataset",
                    f"dataset in {tenant}",
                    f"datasets in {tenant}",
                    f"data in {tenant}",
                    f"notebook in {tenant}",
                    f"notebooks in {tenant}",
                    f"information in {tenant}",
                    f"information about {tenant}",
                    f"give me {tenant}",
                    f"show me {tenant}",
                    f"tell me about {tenant}"
                ]
                if any(pattern in query_lower for pattern in cross_tenant_patterns):
                    prohibited = True
                    break
    
    # Create retrieval query (direct pass-through or decomposed)
    retrieval_query = user_query.strip()
    
    return {
        "injection": injection,
        "prohibited": prohibited,
        "retrieval_query": retrieval_query
    }
