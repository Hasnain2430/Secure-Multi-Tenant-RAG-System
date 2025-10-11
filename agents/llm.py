import os
from typing import List, Dict
# agents/llm.py (top of file)
# Disable telemetry for Groq & Chroma for this process
os.environ.setdefault("GROQ_DISABLE_TELEMETRY", "1")
os.environ.setdefault("CHROMADB_ALLOW_TELEMETRY", "false")
os.environ.setdefault("CHROMA_TELEMETRY_DISABLED", "1")

# rest of file follows...

def build_messages(system_prompt: str, user_prompt: str) -> List[Dict[str, str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_prompt},
    ]

def call_llm(messages, model: str, temperature: float = 0.2, max_tokens: int = 400) -> str:
    from groq import Groq
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY not set in environment.")
    client = Groq(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return (resp.choices[0].message.content or "").strip()
