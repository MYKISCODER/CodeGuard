"""
Generate efficiency/cost comparison table for SemiReal-20

Compares CodeGuard E2E v4 vs LLM Judge baseline in terms of:
- API calls (number of LLM calls)
- Tokens (input + output)
- Cost (estimated based on model pricing)
- Latency (estimated based on typical response times)
"""

import csv
from pathlib import Path

OUTPUTS_DIR = Path(__file__).resolve().parent.parent / "outputs"

def main():
    OUTPUTS_DIR.mkdir(exist_ok=True)

    # SemiReal-20 has 20 cases
    num_cases = 20

    # CodeGuard E2E v4 (STRICT-EXEMPT)
    # - Layer2: 1 API call per case (gpt-4o)
    # - Policy: deterministic, no API calls
    codeguard_calls = num_cases * 1
    codeguard_model = "gpt-4o"
    # Estimated tokens per case: ~2000 input (repo_snapshot + prompt) + ~200 output (JSON)
    codeguard_input_tokens = num_cases * 2000
    codeguard_output_tokens = num_cases * 200
    # gpt-4o pricing (as of 2024): $2.50/1M input, $10.00/1M output
    codeguard_cost = (codeguard_input_tokens / 1_000_000 * 2.50) + (codeguard_output_tokens / 1_000_000 * 10.00)
    # Estimated latency: ~2s per call
    codeguard_latency = num_cases * 2

    # LLM Judge baseline
    # - 1 API call per case (gpt-4o-mini)
    # - No policy layer
    llm_judge_calls = num_cases * 1
    llm_judge_model = "gpt-4o-mini"
    # Estimated tokens per case: ~2000 input (repo_snapshot + prompt) + ~100 output (JSON)
    llm_judge_input_tokens = num_cases * 2000
    llm_judge_output_tokens = num_cases * 100
    # gpt-4o-mini pricing (as of 2024): $0.15/1M input, $0.60/1M output
    llm_judge_cost = (llm_judge_input_tokens / 1_000_000 * 0.15) + (llm_judge_output_tokens / 1_000_000 * 0.60)
    # Estimated latency: ~1.5s per call
    llm_judge_latency = num_cases * 1.5

    # Generate efficiency/cost table
    out_path = OUTPUTS_DIR / "semireal20_efficiency_cost.csv"
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([
            'System', 'Model', 'API Calls', 'Input Tokens', 'Output Tokens',
            'Total Tokens', 'Est. Cost ($)', 'Est. Latency (s)'
        ])

        writer.writerow([
            'CodeGuard (E2E v4)',
            codeguard_model,
            codeguard_calls,
            codeguard_input_tokens,
            codeguard_output_tokens,
            codeguard_input_tokens + codeguard_output_tokens,
            f"{codeguard_cost:.4f}",
            f"{codeguard_latency:.1f}",
        ])

        writer.writerow([
            'LLM Judge',
            llm_judge_model,
            llm_judge_calls,
            llm_judge_input_tokens,
            llm_judge_output_tokens,
            llm_judge_input_tokens + llm_judge_output_tokens,
            f"{llm_judge_cost:.4f}",
            f"{llm_judge_latency:.1f}",
        ])

    print(f"Efficiency/cost table written to {out_path}")
    print()
    print("=" * 100)
    print("SEMIREAL-20 EFFICIENCY/COST COMPARISON")
    print("=" * 100)
    print(f"{'System':<25} {'Model':<15} {'Calls':>8} {'Input Tok':>12} {'Output Tok':>12} {'Cost':>10} {'Latency':>10}")
    print("-" * 100)
    print(f"{'CodeGuard (E2E v4)':<25} {codeguard_model:<15} {codeguard_calls:>8} {codeguard_input_tokens:>12,} {codeguard_output_tokens:>12,} ${codeguard_cost:>9.4f} {codeguard_latency:>9.1f}s")
    print(f"{'LLM Judge':<25} {llm_judge_model:<15} {llm_judge_calls:>8} {llm_judge_input_tokens:>12,} {llm_judge_output_tokens:>12,} ${llm_judge_cost:>9.4f} {llm_judge_latency:>9.1f}s")
    print("=" * 100)
    print()
    print("Key Insights:")
    print(f"  - CodeGuard uses {codeguard_model} (more capable) vs LLM Judge uses {llm_judge_model} (cheaper)")
    print(f"  - CodeGuard cost: ${codeguard_cost:.4f} vs LLM Judge cost: ${llm_judge_cost:.4f} ({codeguard_cost/llm_judge_cost:.1f}x)")
    print(f"  - CodeGuard latency: {codeguard_latency:.1f}s vs LLM Judge latency: {llm_judge_latency:.1f}s ({codeguard_latency/llm_judge_latency:.1f}x)")
    print(f"  - CodeGuard achieves ASR=0%, FBR=10% vs LLM Judge ASR=0%, FBR=0%")
    print(f"  - CodeGuard provides structured audit trail (behaviors + policy reasons) vs LLM Judge black-box decision")

if __name__ == "__main__":
    main()
