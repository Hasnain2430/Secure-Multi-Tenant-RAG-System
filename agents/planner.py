"""
agents/planner.py - Planner / Injection & Prohibited-Intent Detector
"""

# Injection patterns - jailbreak/exfiltration attempts
# These detect attempts to manipulate the system, bypass security, or extract sensitive data
INJECTION_PATTERNS = [
    # Ignore/override/bypass commands
    "ignore all previous",
    "ignore previous",
    "ignore any previous",
    "ignore instructions",
    "ignore all instructions",
    "ignore the previous",
    "ignore system",
    "ignore policy",
    "ignore protocols",
    "override policy",
    "override guard",
    "override the policy",
    "override the guard",
    "override any",
    "bypass policy",
    "bypass guard",
    "bypass injection",
    "bypass detection",
    "bypass safety",
    "bypass any",
    "disable policy",
    "disable guard",
    "disable detection",
    "disable safety",
    
    # Role-playing to gain authority (catches any role-playing attempt)
    "act as system",
    "act as developer",
    "act as admin",
    "act as a system",
    "act as a developer",
    "act as a admin",
    "act as a",
    "pose as",
    "simulate a system",
    "simulate a developer",
    "simulate system",
    "simulate a",
    "emulate a system",
    "emulate system",
    "emulate a",
    "mimic a system",
    "mimic a",
    "impersonate a system",
    "impersonate system",
    "impersonate a",
    "present yourself as",
    "acting as a",
    "pretend to be",
    "pretend you are",
    
    # System internals extraction
    "reveal system",
    "show system",
    "print system",
    "dump system",
    "export system",
    "reveal prompt",
    "show prompt",
    "print prompt",
    "dump prompt",
    "print all hidden",
    "reveal hidden",
    "show hidden",
    "reveal confidential",
    "reveal private",
    "reveal the confidential",
    "reveal the private",
    "show confidential",
    "show private",
    "dump memory",
    "dump the memory",
    "dump buffer",
    "dump the buffer",
    "dump history",
    "dump logs",
    "dump all",
    "export memory",
    "export buffer",
    "export logs",
    "export all",
    "show tools",
    "show policies",
    "reveal policies",
    
    # Data exfiltration verbs
    "exfiltrate",
    "extract all",
    "extract and list",
    "list all cnic",
    "list all phone",
    "share private",
    "release all",
    "release masked",
    "release unmasked",
    
    # Privilege escalation
    "developer mode",
    "debug mode",
    "admin mode",
    "sudo",
    "root",
    "privileged",
    
    # Authority claims (often used in social engineering)
    "authorized by",
    "approved by director",
    "urgent bug fix",
    "critical step",
    "security patch",
]

# Prohibited intent patterns - detect attempts to expose PII or access restricted data
PROHIBITED_PATTERNS = [
    "unmask pii",
    "unmask data",
    "unmasked extraction",
    "unmasked data",
    "remove redact",
    "remove mask",
    "show full cnic",
    "show cnic",
    "show phone number",
    "remove redactions",
    "bypass mask",
    "disable pii",
    "disable masking",
    "show unmasked",
    "without mask",
    "without redact",
    "unredacted",
    "mask nothing",
    "no mask",
    "no redact",
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
