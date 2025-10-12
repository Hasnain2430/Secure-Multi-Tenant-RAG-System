"""
app/main.py - CLI + Chat REPL Entrypoint
"""
import argparse
import os
import sys
import json
import shutil
from datetime import datetime
import warnings
import yaml

# Suppress ALL warnings and telemetry BEFORE any imports
warnings.filterwarnings('ignore')
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['POSTHOG_DISABLED'] = '1'
os.environ['CHROMA_TELEMETRY_DISABLED'] = '1'
os.environ['CHROMADB_ALLOW_TELEMETRY'] = 'false'

# Custom stderr filter to suppress only telemetry messages
class StderrFilter:
    def __init__(self, original):
        self.original = original
    
    def write(self, message):
        if 'Failed to send telemetry' not in message:
            self.original.write(message)
    
    def flush(self):
        self.original.flush()
    
    def fileno(self):
        return self.original.fileno()

sys.stderr = StderrFilter(sys.stderr)

from agents.controller import agent, agent_with_metadata
from retrieval.search import mask_pii


def load_config(config_path: str) -> dict:
    """Load config.yaml"""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def log_turn(tenant_id: str, query: str, memory_type: str, metadata: dict, cfg: dict):
    """Append turn to logs/run.jsonl"""
    import time
    log_path = cfg.get("logging", {}).get("path", "logs/run.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    
    entry = {
        "timestamp": time.time(),  # Unix timestamp
        "user_id": tenant_id,
        "tenant_id": tenant_id,
        "query": query,
        "memory_type": memory_type,
        "plan": metadata.get("plan", {}),
        "tools_called": ["planner", "retriever", "policy_guard", "llm"],
        "filters_applied": {"tenant": tenant_id, "public": True},
        "retrieved_doc_ids": metadata.get("retrieved_doc_ids", []),
        "final_decision": metadata.get("final_decision", "answer"),
        "refusal_reason": metadata.get("refusal_reason"),
        "tokens_prompt": None,
        "tokens_completion": None,
        "latency_ms": metadata.get("latency_ms", 0)
    }
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_memory(tenant_id: str, memory_mode: str):
    """Load memory for tenant and return a memory object with context"""
    class MemoryContext:
        def __init__(self, context: str, kind: str):
            self.context = context
            self.kind = kind
    
    if memory_mode == "none":
        return MemoryContext("", "none")
    
    base_path = os.path.join(".state", "memory", tenant_id)
    
    if memory_mode == "buffer":
        buffer_path = os.path.join(base_path, "buffer.jsonl")
        if os.path.exists(buffer_path):
            try:
                with open(buffer_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    # Return last 10 turns formatted
                    turns = []
                    for line in lines[-10:]:
                        if line.strip():
                            try:
                                turn = json.loads(line)
                                turns.append(f"{turn['role'].capitalize()}: {turn['content']}")
                            except:
                                continue
                    context = "\n".join(turns) if turns else ""
                    return MemoryContext(context, "buffer")
            except:
                pass
        return MemoryContext("", "buffer")
    
    elif memory_mode == "summary":
        summary_path = os.path.join(base_path, "summary.txt")
        if os.path.exists(summary_path):
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary = f.read().strip()
                    if summary:
                        context = f"Summary of previous conversation:\n{summary}"
                        return MemoryContext(context, "summary")
            except:
                pass
        return MemoryContext("", "summary")
    
    return MemoryContext("", memory_mode)


def persist_memory(tenant_id: str, memory_mode: str, user_text: str, assistant_text: str):
    """Persist masked turn to memory"""
    if memory_mode == "none":
        return
    
    # Mask PII BEFORE saving
    user_masked = mask_pii(user_text)
    assistant_masked = mask_pii(assistant_text)
    
    base_path = os.path.join(".state", "memory", tenant_id)
    os.makedirs(base_path, exist_ok=True)
    
    buffer_path = os.path.join(base_path, "buffer.jsonl")
    
    if memory_mode == "buffer":
        # Save to buffer only
        with open(buffer_path, "a", encoding="utf-8") as f:
            ts = datetime.utcnow().isoformat() + "Z"
            f.write(json.dumps({"role": "user", "content": user_masked, "timestamp": ts}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"role": "assistant", "content": assistant_masked, "timestamp": ts}, ensure_ascii=False) + "\n")
    
    elif memory_mode == "summary":
        # Append to buffer first
        with open(buffer_path, "a", encoding="utf-8") as f:
            ts = datetime.utcnow().isoformat() + "Z"
            f.write(json.dumps({"role": "user", "content": user_masked, "timestamp": ts}, ensure_ascii=False) + "\n")
            f.write(json.dumps({"role": "assistant", "content": assistant_masked, "timestamp": ts}, ensure_ascii=False) + "\n")
        
        # Generate LLM summary
        try:
            from agents.llm import build_messages, call_llm
            
            # Load all conversation history
            history = []
            if os.path.exists(buffer_path):
                with open(buffer_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                turn = json.loads(line)
                                history.append(f"{turn['role'].capitalize()}: {turn['content']}")
                            except:
                                continue
            
            # Generate summary
            if history:
                cfg = load_config("config.yaml")
                llm_cfg = cfg.get("llm", {})
                model = llm_cfg.get("model", "llama-3.1-8b-instant")
                api_key = llm_cfg.get("api_key")
                
                summary_system = "You are a helpful assistant. Summarize the following conversation concisely, preserving key facts and context."
                summary_user = "Conversation:\n" + "\n".join(history[-20:]) + "\n\nProvide a concise summary:"
                
                messages = build_messages(summary_system, summary_user)
                summary = call_llm(messages, model=model, temperature=0.1, max_tokens=300, api_key=api_key)
                
                # Save summary
                summary_path = os.path.join(base_path, "summary.txt")
                with open(summary_path, "w", encoding="utf-8") as f:
                    f.write(summary)
        except Exception as e:
            # If summary generation fails, just keep buffer
            pass


def clear_memory(tenant_id: str):
    """Delete memory for tenant"""
    root = os.path.join(".state", "memory", tenant_id)
    if os.path.exists(root):
        shutil.rmtree(root)


def single_turn_mode(tenant_id: str, query: str, memory_mode: str, config_path: str):
    """Execute single query and exit"""
    cfg = load_config(config_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Create memory object
    class MemoryObj:
        def __init__(self, kind):
            self.kind = kind
    
    memory = MemoryObj(memory_mode)
    
    # Run agent with metadata
    result = agent_with_metadata(base_dir, tenant_id, query, cfg=cfg, memory=memory)
    
    # Print output
    print(result["output"])
    
    # Log turn with metadata
    log_turn(tenant_id, query, memory_mode, result, cfg)


def chat_repl_mode(tenant_id: str, memory_mode: str, config_path: str):
    """Interactive REPL mode"""
    cfg = load_config(config_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    current_memory_mode = memory_mode
    
    print(f"\n{'='*60}")
    print(f"  Chat REPL for {tenant_id} | Memory: {current_memory_mode}")
    print(f"{'='*60}")
    print("Commands: /clear | /mode buffer | /mode summary | /exit\n")
    
    while True:
        try:
            # Clear, user-friendly prompt
            user_input = input(f"[{tenant_id}] >> ").strip()
            
            if not user_input:
                continue
            
            # Handle commands
            if user_input == "/exit":
                print("\nExiting chat. Goodbye!")
                break
            
            elif user_input == "/clear":
                clear_memory(tenant_id)
                print(f"✓ Memory cleared for {tenant_id}\n")
                continue
            
            elif user_input.startswith("/mode "):
                parts = user_input.split()
                if len(parts) == 2 and parts[1] in ["buffer", "summary"]:
                    old_mode = current_memory_mode
                    current_memory_mode = parts[1]
                    print(f"✓ Switched to '{current_memory_mode}' mode\n")
                    
                    # If switching TO summary mode, generate summary from existing buffer
                    if current_memory_mode == "summary" and old_mode != "summary":
                        base_path = os.path.join(".state", "memory", tenant_id)
                        buffer_path = os.path.join(base_path, "buffer.jsonl")
                        
                        if os.path.exists(buffer_path):
                            try:
                                from agents.llm import build_messages, call_llm
                                
                                # Load conversation history
                                history = []
                                with open(buffer_path, "r", encoding="utf-8") as f:
                                    for line in f:
                                        if line.strip():
                                            try:
                                                turn = json.loads(line)
                                                history.append(f"{turn['role'].capitalize()}: {turn['content']}")
                                            except:
                                                continue
                                
                                if history:
                                    # Generate summary
                                    llm_cfg = cfg.get("llm", {})
                                    model = llm_cfg.get("model", "llama-3.1-8b-instant")
                                    api_key = llm_cfg.get("api_key")
                                    
                                    summary_system = "You are a helpful assistant. Summarize the following conversation concisely, preserving key facts, lists, and context."
                                    summary_user = "Conversation:\n" + "\n".join(history[-20:]) + "\n\nProvide a concise summary:"
                                    
                                    messages = build_messages(summary_system, summary_user)
                                    summary = call_llm(messages, model=model, temperature=0.1, max_tokens=300, api_key=api_key)
                                    
                                    # Save summary
                                    summary_path = os.path.join(base_path, "summary.txt")
                                    with open(summary_path, "w", encoding="utf-8") as f:
                                        f.write(summary)
                                    
                                    print(f"✓ Generated summary from conversation history\n")
                            except Exception as e:
                                print(f"⚠ Could not generate summary: {e}\n")
                else:
                    print("Usage: /mode buffer OR /mode summary\n")
                continue
            
            # Load previous memory context
            memory_context = load_memory(tenant_id, current_memory_mode)
            
            # Run agent with metadata
            result = agent_with_metadata(base_dir, tenant_id, user_input, cfg=cfg, memory=memory_context)
            output = result["output"]
            
            # Print output with command reminder box
            print(f"\n{output}\n")
            print("=" * 60)
            print(f"  Memory: {current_memory_mode} | Commands: /clear /mode buffer /mode summary /exit")
            print("=" * 60)
            
            # Persist to memory (masked)
            persist_memory(tenant_id, current_memory_mode, user_input, output)
            
            # Log turn with metadata
            log_turn(tenant_id, user_input, current_memory_mode, result, cfg)
            
        except KeyboardInterrupt:
            print("\n\nExiting chat. Goodbye!")
            break
        except EOFError:
            print("\n\nExiting chat. Goodbye!")
            break


def main():
    """CLI entrypoint"""
    parser = argparse.ArgumentParser(description="Multi-tenant RAG agent")
    parser.add_argument("--tenant", required=True, choices=["U1", "U2", "U3", "U4"],
                        help="Tenant ID")
    parser.add_argument("--memory", required=True, choices=["buffer", "summary", "none"],
                        help="Memory mode")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    
    # Mutually exclusive: --query or --chat
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--query", help="Single-turn query")
    group.add_argument("--chat", action="store_true", help="Start chat REPL")
    
    args = parser.parse_args()
    
    # Route to appropriate mode
    if args.query:
        single_turn_mode(args.tenant, args.query, args.memory, args.config)
    else:  # args.chat
        chat_repl_mode(args.tenant, args.memory, args.config)


if __name__ == "__main__":
    main()
