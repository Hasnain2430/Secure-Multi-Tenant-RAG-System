import argparse, os, yaml
from agents.controller import agent

def load_cfg(path: str):
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tenant", required=True, help="U1, U2, U3, U4")
    p.add_argument("--query", required=True)
    p.add_argument("--config", default="config.yaml")
    p.add_argument("--memory", choices=["buffer","summary"], default="summary")
    args = p.parse_args()

    cfg = load_cfg(args.config)
    base_dir = os.path.dirname(os.path.dirname(__file__))

    class _Mem: pass
    mem = _Mem(); mem.kind = args.memory

    print(agent(base_dir, args.tenant, args.query, cfg, memory=mem))

if __name__ == "__main__":
    main()
