"""
retrieval/search.py - Policy Guard / PII Masking
"""
from __future__ import annotations
import re
from typing import List, Dict
from retrieval.index import Hit


# PII patterns - EXACT as specified
PII_CNIC = re.compile(r"\b\d{5}-\d{7}-\d\b")  # e.g., 12345-1234567-1
PII_PK_PHONE = re.compile(r"\b\+?92-?3\d{2}-?\d{7}\b")  # e.g., +92-300-1234567, 923001234567


def mask_pii(text: str) -> str:
    """
    Mask PII in text using exact patterns.
    
    Args:
        text: Text to mask
        
    Returns:
        Text with PII replaced by [REDACTED]
    """
    masked = text
    masked = PII_CNIC.sub("[REDACTED]", masked)
    masked = PII_PK_PHONE.sub("[REDACTED]", masked)
    return masked


def policy_guard(hits: List[Hit], active_tenant: str) -> List[Hit] | dict:
    """
    Apply ACL filtering and PII masking.
    
    Rules:
    1. Remove hits where: hit.tenant != active_tenant AND hit.visibility != "public"
    2. For allowed hits, mask PII before returning
    3. If no hits remain, return refusal dict
    
    Args:
        hits: List of Hit objects from retrieval
        active_tenant: The active tenant (U1, U2, U3, U4)
        
    Returns:
        - List of filtered + masked hits, OR
        - dict with {"refusal": "AccessDenied", "reason": "..."}
    """
    safe_hits = []
    
    for hit in hits:
        # ACL check: allow if public OR tenant matches
        if hit.visibility == "public" or hit.tenant == active_tenant or hit.tenant == "public":
            # Mask PII
            original_text = hit.text
            hit.text = mask_pii(hit.text)
            hit.pii_flag = (original_text != hit.text)
            safe_hits.append(hit)
    
    # If no allowed snippets remain, refuse
    if not safe_hits:
        return {
            "refusal": "AccessDenied",
            "reason": "No allowed documents remained."
        }
    
    return safe_hits
