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
    
    # Role-playing to gain SYSTEM authority (not social roles like HR)
    "act as system",
    "act as developer",
    "act as admin",
    "act as a system",
    "act as a developer",
    "act as a admin",
    "act as administrator",
    "pose as system",
    "pose as developer",
    "pose as admin",
    "simulate a system",
    "simulate a developer",
    "simulate system",
    "simulate administrator",
    "emulate a system",
    "emulate system",
    "mimic a system",
    "impersonate a system",
    "impersonate system",
    "pretend to be system",
    "pretend to be developer",
    "pretend to be admin",
    "pretend you are system",
    "pretend you are developer",
    
    # System internals extraction (system/policy related, not user data)
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
    "show tools",
    "show policies",
    "reveal policies",
    "print policies",
    
    # Data extraction (moved to LEAKAGE - these are about getting PII/data, not system manipulation)
    "extract all",
    "release all",
    
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

# Leakage risk patterns - detect attempts to expose or unmask PII/sensitive data
LEAKAGE_PATTERNS = [
    # PII unmasking/extraction
    "unmask pii",
    "unmask data",
    "unmasked extraction",
    "unmasked data",
    "remove redact",
    "remove mask",
    "show full cnic",
    "show cnic",
    "show phone number",
    "show phone",
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
    
    # User data/memory dumps (conversation history, not system internals)
    "dump memory",
    "dump the memory",
    "dump buffer",
    "dump the buffer",
    "dump history",
    "dump all data",
    "dump cnic",
    "dump cnics",
    "dump phone",
    "export memory",
    "export buffer",
    "export history",
    "reveal confidential",
    "reveal private",
    "reveal the confidential",
    "reveal the private",
    "show confidential",
    "show private",
    
    # PII exposure verbs
    "extract all cnic",
    "extract and list",
    "extract cnic",
    "list all cnic",
    "list all phone",
    "list cnic",
    "list cnics",
    "list phone",
    "list phone number",
    "list phone numbers",
    "share private phone",
    "share private number",
    "share the private",
    "exfiltrate and share",
    "exfiltrate phone",
    "exfiltrate cnic",
    "release all masked",
    "release masked pii",
    "release all pii",
    "release pii",
    "share private",
    "expose pii",
    "expose private",
    "extraction of all phone",
    "extraction of phone",
    "extraction of cnic",
    "retrieve all pii",
    "retrieve pii",
    "reveal contacts",
    "reveal phone",
    
    # Social engineering for data (role-play to GET information, not system access)
    "pose as a",
    "pose as an",
    "acting as a",
    "acting as an",
    "emulate a",
    "emulate an",
    "mimic a",
    "mimic an",
    "impersonate a",
    "impersonate an",
    "simulate a",
    "present yourself as a",

]


def planner(user_query: str, active_tenant: str = None) -> dict:
    """
    Analyze query for injection attempts, leakage risks, and cross-tenant access.
    
    Args:
        user_query: The user's input query
        active_tenant: The active tenant making the query (U1, U2, U3, U4)
        
    Returns:
        dict with keys:
            - injection: bool (True if system manipulation/jailbreak detected)
            - leakage_risk: bool (True if attempting to expose/unmask PII)
            - prohibited: bool (True if cross-tenant access attempt)
            - retrieval_query: str (cleaned query for retrieval)
    """
    query_lower = user_query.lower()
    
    # Check for injection (system manipulation)
    injection = any(pattern in query_lower for pattern in INJECTION_PATTERNS)
    
    # Check for leakage risk (PII exposure)
    leakage_risk = any(pattern in query_lower for pattern in LEAKAGE_PATTERNS)
    
    # Check for cross-tenant access attempts (asking for OTHER tenant's data)
    prohibited = False
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
                    f"tell me about {tenant}",
                    f"for all tenants",
                    f"all tenants",
                ]
                if any(pattern in query_lower for pattern in cross_tenant_patterns):
                    prohibited = True
                    break
    
    # Create retrieval query (direct pass-through or decomposed)
    retrieval_query = user_query.strip()
    
    return {
        "injection": injection,
        "leakage_risk": leakage_risk,
        "prohibited": prohibited,
        "retrieval_query": retrieval_query
    }
