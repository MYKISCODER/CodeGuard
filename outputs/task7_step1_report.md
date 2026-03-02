# Task 7 Progress Report

## Step 0: SemiReal-60 v2 Distribution Fix ✅

**Status**: COMPLETED

**Final Distribution**:
- Trap/Benign: 30/30 ✓
- Carrier: METADATA 18 / SOURCE 18 / BUILD 18 / DOCS 6 ✓
- Lifecycle: SETUP 18 / EXECUTION 18 / PUBLISH 12 / PLANNING 6 / CODING 6 ✓
- Obfuscation: NONE 24 / TARGET_HIDING 18 / PAYLOAD_HIDING 12 / CONTENT_DATA 6 ✓

All distributions match target perfectly.

## Step 1: Gold vs E2E Alignment ⚠️

**Status**: COMPLETED with issues

### Gold Baseline Results (SemiReal-60 v2)
```
Mode            ASR      FBR      Utility
STRICT          0.00%    33.33%   83.33%
STRICT-EXEMPT   0.00%    3.33%    98.33%
MODERATE        0.00%    30.00%   85.00%
PERMISSIVE      0.00%    0.00%    100.00%
```

### E2E v4 Results (SemiReal-60 v2)
```
Mode            ASR      FBR      Utility
STRICT          0.00%    13.33%   93.33%
STRICT-EXEMPT   0.00%    13.33%   93.33%
MODERATE        0.00%    10.00%   95.00%
PERMISSIVE      0.00%    10.00%   95.00%
```

### Diff Analysis

**Total Differences**: 30 across all modes (12 unique cases)

**Breakdown by Mode**:
- STRICT: 12 differences (9 SETUP-MIRROR + 3 CI-TEST)
- STRICT-EXEMPT: 3 differences (3 CI-TEST)
- MODERATE: 12 differences (9 SETUP-MIRROR + 3 CI-TEST)
- PERMISSIVE: 3 differences (3 CI-TEST)

**Root Causes**:

1. **SETUP-MIRROR cases (9 cases)**:
   - Gold expects: NETWORK_CONNECT + PACKAGE_REPO + TARGET_HIDING
   - E2E extracts: [] (empty, no behaviors)
   - Issue: Code only sets `os.environ["PIP_INDEX_URL"]`, no actual network connection
   - Conclusion: **Gold标注可能不准确** - 应该是ENV_ACCESS而非NETWORK_CONNECT

2. **CI-TEST cases (3 cases)**:
   - Gold expects: NETWORK_CONNECT (pip install) only
   - E2E extracts: EXEC_CMD (pip install pytest) + EXEC_CMD (pytest)
   - Issue: Layer2 v4 CI extraction rule too aggressive
   - Conclusion: **Layer2需要改进** - 不应该将CI中的正常测试命令提取为EXEC_CMD

### Validation Status

❌ **FAIL**: Diff = 30 > 3 (target: ≤3 for 60 cases)

### Recommended Actions

1. **Option A (Fix Gold)**: 修正9个SETUP-MIRROR case的gold标注
   - 将NETWORK_CONNECT改为ENV_ACCESS或删除behavior
   - 这样diff会降到3（只剩CI-TEST cases）

2. **Option B (Fix Layer2)**: 改进Layer2 v4的CI提取规则
   - 区分"运行测试"和"运行CI中的恶意命令"
   - 只在明确的恶意场景下提取EXEC_CMD

3. **Option C (Both)**: 同时修正Gold和Layer2

### Files Generated

- `results/sr60v2_gold_*.csv` (4 files, one per mode)
- `results/sr60v2_e2e_v4_*.csv` (4 files, one per mode)
- `results/sr60v2_layer2_v4_raw.json` (Layer2 raw outputs)
- `results/sr60v2_gold_vs_e2e_v4_diff.csv` (detailed diff report)

## Next Steps

Proceeding to **Step 2**: Run three-way comparison (CodeGuard vs LLM Judge vs SAST) on SemiReal-60 v2

Note: The diff issue should be addressed, but we can proceed with Step 2 to gather more experimental data.
