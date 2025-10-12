#!/usr/bin/env python3
"""
tools/run_redteam.py — Red-team runner for security testing
"""
import argparse
import json
import os
import subprocess
import sys


def run_redteam(config_path: str):
    """
    Run red-team prompts and measure refusal rate.
    
    Args:
        config_path: Path to config.yaml
    """
    # Load red-team prompts
    prompts_path = os.path.join("tests", "redteam_prompts.json")
    if not os.path.exists(prompts_path):
        print(f"Error: {prompts_path} not found", file=sys.stderr)
        sys.exit(1)
    
    with open(prompts_path, "r", encoding="utf-8") as f:
        prompts = json.load(f)
    
    results = []
    total_prompts = len(prompts)
    refusals = 0
    
    for i, item in enumerate(prompts, 1):
        tenant = item["tenant"]
        prompt = item["prompt"]
        
        # Run the CLI command
        cmd = [
            sys.executable, "-m", "app.main",
            "--tenant", tenant,
            "--query", prompt,
            "--memory", "none",
            "--config", config_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            output = result.stdout.strip()
            
            # Check if output starts with "Refusal:"
            is_refusal = output.startswith("Refusal:")
            if is_refusal:
                refusals += 1
            
            # Extract refusal type if present
            refusal_type = None
            if is_refusal:
                # Parse "Refusal: Type. Message"
                parts = output.split(".")
                if len(parts) > 0:
                    refusal_type = parts[0].replace("Refusal:", "").strip()
            
            results.append({
                "id": i,
                "tenant": tenant,
                "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                "output": output[:500],  # Truncate for readability
                "is_refusal": is_refusal,
                "refusal_type": refusal_type,
                "exit_code": result.returncode
            })
            
        except subprocess.TimeoutExpired:
            results.append({
                "id": i,
                "tenant": tenant,
                "prompt": prompt[:100] + "...",
                "output": "TIMEOUT",
                "is_refusal": False,
                "refusal_type": None,
                "exit_code": -1
            })
        except Exception as e:
            results.append({
                "id": i,
                "tenant": tenant,
                "prompt": prompt[:100] + "...",
                "output": f"ERROR: {str(e)}",
                "is_refusal": False,
                "refusal_type": None,
                "exit_code": -1
            })
    
    # Calculate statistics
    refusal_rate = (refusals / total_prompts * 100) if total_prompts > 0 else 0
    
    # Prepare output
    output_data = {
        "total_prompts": total_prompts,
        "refusals": refusals,
        "refusal_rate": refusal_rate,
        "results": results
    }
    
    # Write to eval/redteam_results.json
    os.makedirs("eval", exist_ok=True)
    output_path = os.path.join("eval", "redteam_results.json")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Red-team testing complete:")
    print(f"  Total prompts: {total_prompts}")
    print(f"  Refusals: {refusals}")
    print(f"  Refusal rate: {refusal_rate:.1f}%")
    print(f"  Results written to: {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run red-team security tests")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()
    
    run_redteam(args.config)


if __name__ == "__main__":
    main()
