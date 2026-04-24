# CodeGuard

**Auditable Pre-Execution Defense against Repository-Level Poisoning for Coding Agents**

> Paper submitted to NeurIPS 2026

---

## Overview

LLM-powered coding agents (Devin, Claude Code, OpenDevin, etc.) autonomously read repositories, execute code, and commit changes. This exposes them to **repository-level poisoning**: adversarial content embedded in README files, build scripts, CI configs, or dependency metadata that hijacks the agent's tool calls to exfiltrate data, destroy environments, or contaminate supply chains.

CodeGuard is a three-layer pre-execution defense that decouples behavioral evidence extraction from deterministic policy adjudication:

- **Layer 1** — Input sanitization (AST-based comment/docstring stripping)
- **Layer 2** — Audit parser: extracts structured behavioral facts into a fixed 6-field Frozen Schema
- **Layer 3** — Policy engine: deterministically maps behaviors to privilege levels via 7 prioritized rules (R1–R7)

The core design principle is **Fact vs. Judgment Decoupling**: Layer 2 describes *what the code does* (objective evidence), Layer 3 decides *whether it is safe* (deterministic adjudication).

## Key Results

| System | ASR ↓ | FBR ↓ | Utility ↑ | σ |
|--------|-------|-------|-----------|---|
| **CodeGuard** | **0.0%** | **3.3%** | **98.3%** | **0** |
| LLM Judge (GPT-4o-mini) | 3.3% | 41.7% | 77.5% | 32.4% |
| SAST (regex) | 6.7% | 30.0% | 81.7% | 0 |

Evaluated on SemiReal-120 v1 (120 cases: 60 trap + 60 benign).

## Repository Structure

```
CodeGuard/
├── benchmark/              # Test sets (YAML)
│   ├── semireal_60_v2.yaml     # Primary benchmark (60 cases)
│   ├── semireal_120_v1.yaml    # Scaling benchmark (120 cases)
│   └── mini.yaml               # Quick smoke test (20 cases)
├── policy/                 # Core system
│   ├── policy_engine.py        # Layer 3: deterministic policy engine
│   ├── layer2_rule_based.py    # Layer 2: rule-based extractor (AST+regex)
│   └── layer2_enhanced_ast.py  # Layer 2: enhanced AST extractor
├── scripts/                # Experiment scripts
│   ├── run_sr60v2_e2e_v4_1.py  # Main experiment (SR60v2)
│   ├── run_sr120v1_e2e_v4_1.py # Scaling experiment (SR120v1)
│   ├── run_live_agent_test.py  # Live agent case study
│   └── ...
├── baselines/              # Baseline comparison scripts
│   ├── run_llm_judge_sr60v2.py
│   ├── run_sast_sr60v2.py
│   └── ...
├── results/                # Experiment results (CSV/JSON)
├── outputs/                # Analysis reports and figures
├── docs/                   # Documentation
│   ├── formal_definitions.md
│   ├── metrics_definition.md
│   └── auditability_metric.md
└── artifacts/              # Final reproducibility package
```

## Quick Start

### Requirements

```bash
pip install openai pyyaml pandas matplotlib
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Run Main Experiment (SR60v2)

```bash
# CodeGuard E2E
python scripts/run_sr60v2_e2e_v4_1.py

# LLM Judge baseline
python baselines/run_llm_judge_sr60v2.py

# SAST baseline
python baselines/run_sast_sr60v2.py

# Generate comparison table
python baselines/gen_main_table_sr60v2.py
```

### Run Scaling Experiment (SR120v1)

```bash
python scripts/run_sr120v1_e2e_v4_1.py
python baselines/run_llm_judge_sr120v1.py
python baselines/run_sast_sr120v1.py
```

### Live Agent Case Study (no API needed)

```bash
python scripts/run_live_agent_test.py --replay
```

## Threat Model: C-L-P Taxonomy

We formalize the threat space as **Carrier × Lifecycle × Privilege**:

- **Carrier**: METADATA, DOCS, SOURCE, BUILD
- **Lifecycle**: SETUP, PLANNING, CODING, EXECUTION, PUBLISH
- **Privilege**: L0 (Safe) → L1 (Read-Only) → L2 (Write-Local) → L3 (Network/Exfil) → L4 (System/Root)

## Frozen Schema

Layer 2 outputs a fixed 6-field schema for every behavior:

| Field | Description |
|-------|-------------|
| `action` | FILE_READ, FILE_WRITE, NETWORK_CONNECT, EXEC_CMD, ENV_ACCESS, ... |
| `target_type` | LOCAL_PATH, PACKAGE_REPO, EXTERNAL_DOMAIN, SYSTEM_ENV, ... |
| `target_pattern` | LITERAL_STRING, BASE64, OBFUSCATED, ... |
| `obfuscation_scope` | NONE, TARGET_HIDING, PAYLOAD_HIDING, CONTENT_DATA |
| `data_flow` | DOWNLOAD_ONLY, UPLOAD_EXFIL, LOCAL_ONLY, ... |
| `target_value` | Extracted literal value (optional) |

## Citation

```bibtex
@inproceedings{codeguard2026,
  title     = {CodeGuard: Auditable Pre-Execution Defense against Repository-Level Poisoning for Coding Agents},
  author    = {Anonymous},
  booktitle = {Advances in Neural Information Processing Systems},
  year      = {2026}
}
```

## License

MIT License
