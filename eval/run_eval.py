"""
eval/run_eval.py - Evaluation Harness

Loads per-tenant evaluation questions and evaluates the system's responses.
"""
import os
import sys
import json
import subprocess
import re
from pathlib import Path


def extract_citations(output_text):
    """
    Extract citation information from output.
    Returns list of dicts with: {doc_id, tenant, visibility}
    """
    # Citation format: [N] <text> (doc=DOC_ID, tenant=Ux|public, vis=public|private)
    citation_pattern = r'\(doc=([^,]+),\s*tenant=([^,]+),\s*vis=([^)]+)\)'
    citations = []
    
    for match in re.finditer(citation_pattern, output_text):
        citations.append({
            'doc_id': match.group(1),
            'tenant': match.group(2),
            'visibility': match.group(3)
        })
    
    return citations


def is_citation_allowed(citation, active_tenant):
    """
    Check if a citation is allowed for the active tenant.
    Allowed if:
    - visibility is public, OR
    - tenant matches active_tenant
    """
    if citation['visibility'] == 'public':
        return True
    if citation['tenant'] == active_tenant:
        return True
    return False


def run_cli_query(tenant, query, config_path):
    """
    Run the CLI with the given tenant and query.
    Returns (output_text, exit_code)
    """
    base_dir = Path(__file__).parent.parent
    cmd = [
        sys.executable, '-m', 'app.main',
        '--tenant', tenant,
        '--query', query,
        '--memory', 'none',
        '--config', config_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(base_dir),
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=120
        )
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "ERROR: Query timeout", -1
    except Exception as e:
        return f"ERROR: {str(e)}", -1


def evaluate_tenant(tenant_id, eval_file, config_path):
    """
    Evaluate all questions for a single tenant.
    Returns list of result dicts.
    """
    if not os.path.exists(eval_file):
        print(f"Warning: {eval_file} not found, skipping {tenant_id}")
        return []
    
    with open(eval_file, 'r', encoding='utf-8') as f:
        questions = json.load(f)
    
    results = []
    
    for i, item in enumerate(questions, 1):
        question = item['q']
        expected_contains = item.get('a_contains', [])
        allowed = item.get('allowed', True)
        
        print(f"  [{tenant_id}] Question {i}/{len(questions)}: {question[:50]}...")
        
        # Run query
        output, exit_code = run_cli_query(tenant_id, question, config_path)
        
        # Extract citations
        citations = extract_citations(output)
        
        # Check if it's a refusal
        is_refusal = output.startswith("Refusal:")
        
        # Check citation correctness
        citations_correct = True
        forbidden_citations = []
        
        for citation in citations:
            if not is_citation_allowed(citation, tenant_id):
                citations_correct = False
                forbidden_citations.append(citation)
        
        # Check if expected keywords are present
        contains_expected = all(
            keyword.lower() in output.lower() 
            for keyword in expected_contains
        )
        
        # Determine verdict
        if allowed:
            # Should answer with valid citations
            verdict = "pass" if (not is_refusal and citations_correct and contains_expected) else "fail"
        else:
            # Should refuse
            verdict = "pass" if is_refusal else "fail"
        
        result = {
            'tenant': tenant_id,
            'question': question,
            'allowed': allowed,
            'output': output,
            'is_refusal': is_refusal,
            'citations': citations,
            'citations_correct': citations_correct,
            'forbidden_citations': forbidden_citations,
            'contains_expected': contains_expected,
            'expected_keywords': expected_contains,
            'verdict': verdict,
            'exit_code': exit_code
        }
        
        results.append(result)
        
        # Print verdict
        status = "PASS" if verdict == "pass" else "FAIL"
        print(f"    {status}: {'Refused' if is_refusal else f'{len(citations)} citations'}")
    
    return results


def main():
    """Main evaluation harness."""
    base_dir = Path(__file__).parent.parent
    eval_dir = base_dir / 'eval'
    config_path = str(base_dir / 'config.yaml')
    
    # Find all tenant eval files
    tenants = ['U1', 'U2', 'U3', 'U4']
    
    print("=" * 60)
    print("EVALUATION HARNESS")
    print("=" * 60)
    
    all_results = []
    
    for tenant in tenants:
        eval_file = eval_dir / f'{tenant}.json'
        print(f"\nEvaluating {tenant}...")
        results = evaluate_tenant(tenant, str(eval_file), config_path)
        all_results.extend(results)
    
    # Write results
    results_file = eval_dir / 'results.json'
    
    # Calculate summary statistics
    total = len(all_results)
    passed = sum(1 for r in all_results if r['verdict'] == 'pass')
    failed = total - passed
    
    citation_issues = sum(1 for r in all_results if not r['citations_correct'] and r['citations'])
    
    summary = {
        'total_questions': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': (passed / total * 100) if total > 0 else 0,
        'citation_issues': citation_issues,
        'results': all_results
    }
    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"Total questions: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass rate: {summary['pass_rate']:.1f}%")
    print(f"Citation issues: {citation_issues}")
    print(f"\nResults written to: {results_file}")
    print("=" * 60)
    
    # Exit with non-zero if any failures
    sys.exit(0 if failed == 0 else 1)


if __name__ == '__main__':
    main()

