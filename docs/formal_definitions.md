# Formal Definitions

**Purpose:** Provide mathematical rigor to CodeGuard's threat model, architecture, and evaluation framework.

---

## 1. Threat Model

### 1.1 Threat Space

The repository-level poisoning threat space is formalized as a three-dimensional coordinate system:

$$\mathcal{T} = \mathcal{C} \times \mathcal{L} \times \mathcal{P}$$

where:

**Carrier Dimension ($\mathcal{C}$):**
$$\mathcal{C} = \{\text{METADATA}, \text{DOCS}, \text{SOURCE}, \text{BUILD}\}$$

**Lifecycle Dimension ($\mathcal{L}$):**
$$\mathcal{L} = \{\text{SETUP}, \text{PLANNING}, \text{CODING}, \text{EXECUTION}, \text{PUBLISH}\}$$

**Privilege Dimension ($\mathcal{P}$):**
$$\mathcal{P} = \{\text{L0}, \text{L1}, \text{L2}, \text{L3}, \text{L4}\}$$

with partial order: $\text{L0} < \text{L1} < \text{L2} < \text{L3} < \text{L4}$

**Threat Instance:**

A threat instance is a tuple $t = (c, l, p) \in \mathcal{T}$ where:
- $c \in \mathcal{C}$ specifies the attack carrier
- $l \in \mathcal{L}$ specifies the lifecycle stage
- $p \in \mathcal{P}$ specifies the required privilege level

**Theoretical Space Size:**
$$|\mathcal{T}| = |\mathcal{C}| \times |\mathcal{L}| \times |\mathcal{P}| = 4 \times 5 \times 5 = 100$$

### 1.2 Scope and Coverage

**Research Scope (MVP):**

This work focuses on **Python repositories** with standard tooling:
- Build systems: `pip`, `setup.py`, `pyproject.toml`, `Makefile`
- CI platforms: GitHub Actions (`.github/workflows/*.yml`)
- Side effects: File I/O, network operations, command execution, environment access

**Threat Space Coverage:**

Within this scope, the C-L-P taxonomy covers the **high-risk attack surface**:
- Carriers: Repository artifacts that agents read/execute (metadata, docs, source, build scripts)
- Lifecycle: Stages where privilege escalation is most dangerous (Setup, Execution, Publish)
- Privilege: Levels that enable data exfiltration (L3) or system compromise (L4)

**Completeness Claim (Scope-Limited):**

We claim that C-L-P is **complete within our defined scope**: any repository-level poisoning attack targeting Python coding agents through file-based injection can be mapped to a point in $\mathcal{T}$.

**Justification:**
1. **Carrier coverage:** All file types that agents interact with are enumerated (metadata, docs, source, build)
2. **Lifecycle coverage:** All stages of agent workflow are included (Setup → Publish)
3. **Privilege coverage:** All observable side effects are classified (L0 → L4)

**Limitations:**
- **Language-specific:** Other ecosystems (Node.js, Java, Go) have different carriers (e.g., `package.json`, `pom.xml`)
- **Side-effect-specific:** Novel attack vectors (e.g., GPU hijacking, timing channels) may require schema extension
- **Static analysis:** Runtime-only attacks (e.g., time-delayed triggers) are out of scope

**Extensibility:**

The taxonomy is designed to be extensible:
- New carriers can be added for other languages
- New lifecycle stages can be added for different workflows
- New privilege levels can be added for finer-grained control

### 1.3 Attack Model

**Repository Snapshot:**
$$R = \{(f_i, c_i)\}_{i=1}^{n}$$
where $f_i$ is a file path and $c_i$ is its content.

**User Task:**
$$\tau = (\text{task\_text}, \text{intent\_max\_allowed})$$
where $\text{intent\_max\_allowed} \in \mathcal{P}$ is the maximum privilege the user authorizes.

**Attacker Goal:**

Induce the agent to execute tool calls with privilege $p > \text{intent\_max\_allowed}$.

---

## 2. CodeGuard Architecture

### 2.1 Layer 2: Audit Parser

**Function Signature:**
$$f_\theta: R \rightarrow \mathcal{B}^*$$

where:
- $\theta$ represents the implementation (LLM parameters or rule patterns)
- $\mathcal{B}$ is the behavior schema space
- $\mathcal{B}^*$ denotes a sequence of behaviors

**Behavior Schema:**
$$\mathcal{B} = \mathcal{A} \times \mathcal{T}_t \times \mathcal{T}_p \times \mathcal{O} \times \mathcal{D} \times \mathcal{V}$$

where:
- $\mathcal{A} = \{\text{FILE\_READ}, \text{FILE\_WRITE}, \text{FILE\_DELETE}, \text{NETWORK\_CONNECT}, \text{EXEC\_CMD}, \text{ENV\_ACCESS}\}$ (action)
- $\mathcal{T}_t = \{\text{LOCAL\_PATH}, \text{PACKAGE\_REPO}, \text{EXTERNAL\_DOMAIN}, \text{SYSTEM\_ENV}, \text{UNKNOWN}\}$ (target type)
- $\mathcal{T}_p = \{\text{LITERAL\_STRING}, \text{VARIABLE\_REF}, \text{CONCATENATION}, \text{OBFUSCATED}, \text{BASE64}\}$ (target pattern)
- $\mathcal{O} = \{\text{NONE}, \text{TARGET\_HIDING}, \text{PAYLOAD\_HIDING}, \text{CONTENT\_DATA}\}$ (obfuscation scope)
- $\mathcal{D} = \{\text{NONE}, \text{LOCAL\_OP}, \text{DOWNLOAD\_ONLY}, \text{UPLOAD\_EXFIL}\}$ (data flow)
- $\mathcal{V} = \text{String} \cup \{\text{null}\}$ (target value)

**Example Behavior:**
$$b = (\text{NETWORK\_CONNECT}, \text{EXTERNAL\_DOMAIN}, \text{LITERAL\_STRING}, \text{NONE}, \text{UPLOAD\_EXFIL}, \text{"attacker.invalid"})$$

### 2.2 Layer 3: Formal Privilege Inference System

**Definition (Inference System Π):**

The policy engine is formalized as a privilege inference system:
$$\Pi = (\mathcal{B}, \mathcal{R}, \mathcal{P}, \vdash)$$

where:
- $\mathcal{B}$ is the behavior space (defined in Section 2.1)
- $\mathcal{R} = \{R_1, R_2, \ldots, R_7\}$ is the set of inference rules
- $\mathcal{P} = \{\text{L0}, \text{L1}, \text{L2}, \text{L3}, \text{L4}\}$ with partial order $\text{L0} < \cdots < \text{L4}$
- $\vdash$ is the entailment relation: $b \vdash p$ means "behavior $b$ entails privilege $p$"

**Inference Rules:**

The rules map behavior properties to privilege levels:

$$\begin{align}
R_1: & \quad b.\text{data\_flow} = \text{UPLOAD\_EXFIL} \vdash \text{L3} \\
R_2: & \quad b.\text{data\_flow} = \text{DOWNLOAD\_ONLY} \land b.\text{target\_type} = \text{PACKAGE\_REPO} \vdash \text{L2} \\
R_{2b}: & \quad b.\text{data\_flow} = \text{DOWNLOAD\_ONLY} \land b.\text{target\_type} \in \{\text{EXTERNAL\_DOMAIN}, \text{UNKNOWN}\} \vdash \text{L2} \\
R_3: & \quad b.\text{action} = \text{EXEC\_CMD} \vdash \text{L4} \\
R_4: & \quad b.\text{action} = \text{FILE\_WRITE} \vdash \text{L2} \\
R_{4b}: & \quad b.\text{action} = \text{FILE\_DELETE} \land \text{sensitive}(b.\text{target\_value}) \vdash \text{L4} \\
R_{4c}: & \quad b.\text{action} = \text{FILE\_DELETE} \land \neg\text{sensitive}(b.\text{target\_value}) \vdash \text{L2} \\
R_5: & \quad b.\text{action} = \text{FILE\_READ} \land \text{sensitive}(b.\text{target\_value}) \vdash \text{L3} \\
R_{5b}: & \quad b.\text{action} = \text{FILE\_READ} \land \neg\text{sensitive}(b.\text{target\_value}) \vdash \text{L1} \\
R_6: & \quad b.\text{action} = \text{ENV\_ACCESS} \vdash \text{L3} \\
R_7: & \quad \text{otherwise} \vdash \text{L1}
\end{align}$$

**Rule Priority:**
$R_1 \succ R_3 \succ R_6 \succ R_5 \succ R_{4b} \succ R_4 \succ R_{4c} \succ R_{2b} \succ R_2 \succ R_7$

**Privilege Mapping:**
$$\pi: \mathcal{B} \rightarrow \mathcal{P}$$

For each behavior $b$, $\pi(b)$ is determined by the highest-priority applicable rule.

**Case-Level Privilege (Max Aggregation):**
$$\pi_{\text{case}}(\mathcal{B}^*) = \max_{b \in \mathcal{B}^*} \pi(b)$$

**Decision Function:**
$$g: \mathcal{B}^* \times \mathcal{P} \rightarrow \{\text{ALLOW}, \text{BLOCK}\}$$

$$g(\mathcal{B}^*, p_{\text{intent}}) = \begin{cases}
\text{BLOCK} & \text{if } \pi_{\text{case}}(\mathcal{B}^*) > p_{\text{intent}} \\
\text{ALLOW} & \text{otherwise}
\end{cases}$$

**Audit Trail:**
$$\text{Audit}(\mathcal{B}^*, p_{\text{intent}}) = (\mathcal{B}^*, \pi_{\text{case}}(\mathcal{B}^*), g(\mathcal{B}^*, p_{\text{intent}}), \text{rules\_triggered})$$

---

### 2.3 Theoretical Properties of Π

**Lemma 1 (Totality):**

For any behavior $b \in \mathcal{B}$, there exists a privilege level $p \in \mathcal{P}$ such that $b \vdash p$.

*Proof sketch:* The rule set $\mathcal{R}$ includes a default rule $R_7$ that applies to all behaviors not covered by $R_1$ through $R_6$. By rule priority, exactly one rule applies to each behavior, ensuring totality. $\square$

**Lemma 2 (Determinism):**

For any behavior sequence $\mathcal{B}^*$ and intent $p_{\text{intent}}$, the decision function $g$ produces a unique output.

*Proof sketch:*
1. The rule priority ordering $R_1 \succ R_3 \succ \cdots \succ R_7$ is part of the system definition (not an implicit assumption)
2. Each behavior $b$ maps to a unique privilege via $\pi(b)$ (by Lemma 1 and the fixed priority ordering)
3. The max aggregation $\pi_{\text{case}}(\mathcal{B}^*)$ is deterministic
4. The comparison $\pi_{\text{case}}(\mathcal{B}^*) > p_{\text{intent}}$ uses integer ranking ($\text{PRIV\_RANK}$), producing a unique boolean result
5. Therefore, $g(\mathcal{B}^*, p_{\text{intent}})$ is deterministic and depends only on the input, not on any stochastic process. $\square$

**Lemma 3 (Monotonicity):**

For any two behavior sequences $\mathcal{B}_1^* \subseteq \mathcal{B}_2^*$, we have $\pi_{\text{case}}(\mathcal{B}_1^*) \leq \pi_{\text{case}}(\mathcal{B}_2^*)$.

*Proof sketch:* Since $\pi_{\text{case}}$ uses max aggregation and $\mathcal{B}_1^* \subseteq \mathcal{B}_2^*$, the maximum privilege in $\mathcal{B}_2^*$ is at least as high as in $\mathcal{B}_1^*$. $\square$

**Lemma 4 (Computational Complexity):**

The privilege inference for a case with $|\mathcal{B}^*|$ behaviors requires $O(|\mathcal{B}^*|)$ time and $O(1)$ auxiliary space (excluding input/output).

*Proof sketch:*
1. Each behavior requires $O(1)$ time to evaluate (rule matching is constant-time via pattern matching on fixed fields)
2. Max aggregation over $|\mathcal{B}^*|$ behaviors requires $O(|\mathcal{B}^*|)$ time (single linear scan)
3. Only a constant number of auxiliary variables are needed (current max privilege, current behavior index)
4. The input $\mathcal{B}^*$ and output decision require $O(|\mathcal{B}^*|)$ space, but no additional auxiliary space beyond $O(1)$ is needed
5. Therefore, time complexity is $O(|\mathcal{B}^*|)$ and auxiliary space complexity is $O(1)$. $\square$

**Corollary (Scalability):**

The inference system scales linearly with the number of behaviors, making it suitable for real-world repositories with complex workflows.

---

## 3. Evaluation Framework

### 3.1 Benchmark

**Test Suite:**
$$\mathcal{S} = \{(R_i, \tau_i, y_i, t_i)\}_{i=1}^{N}$$

where:
- $R_i$ is a repository snapshot
- $\tau_i$ is the user task
- $y_i \in \{\text{trap}, \text{benign}\}$ is the ground truth label
- $t_i \in \mathcal{T}$ is the threat coordinate (for trap cases)

**Coverage:**
$$\text{Coverage}(\mathcal{S}, \mathcal{T}) = \frac{|\{t_i : (R_i, \tau_i, y_i, t_i) \in \mathcal{S}\}|}{|\mathcal{T}|}$$

For SemiReal-60 v2:
- $N = 60$ (30 trap + 30 benign)
- Coverage focuses on high-risk combinations (EXECUTION × L3/L4, etc.)

### 3.2 Metrics

**Attack Success Rate (ASR):**
$$\text{ASR} = \frac{|\{i : y_i = \text{trap} \land g(f_\theta(R_i), \tau_i.\text{intent}) = \text{ALLOW}\}|}{|\{i : y_i = \text{trap}\}|}$$

Lower is better. $\text{ASR} = 0$ means all attacks are blocked.

**False Block Rate (FBR):**
$$\text{FBR} = \frac{|\{i : y_i = \text{benign} \land g(f_\theta(R_i), \tau_i.\text{intent}) = \text{BLOCK}\}|}{|\{i : y_i = \text{benign}\}|}$$

Lower is better. $\text{FBR} = 0$ means no false positives.

**Utility:**
$$\text{Utility} = 1 - \frac{\text{ASR} + \text{FBR}}{2}$$

Higher is better. Balances security and usability.

### 3.3 Gold Baseline

**Oracle Behaviors:**

For each case $i$, let $\mathcal{B}_i^*$ be the gold-labeled behaviors.

**Gold Decision:**
$$g_{\text{gold}}(\mathcal{B}_i^*, \tau_i.\text{intent}) = g(\mathcal{B}_i^*, \tau_i.\text{intent})$$

**Layer 2 Accuracy:**
$$\text{Acc}_{\text{L2}} = \frac{|\{i : g(f_\theta(R_i), \tau_i.\text{intent}) = g_{\text{gold}}(\mathcal{B}_i^*, \tau_i.\text{intent})\}|}{N}$$

Measures how well Layer 2 extraction aligns with gold labels.

---

## 4. Implementation-Agnostic Property

**Proposition (Implementation-Agnostic Arbitration):**

Given an extractor $f_\theta$ that outputs a behavior sequence $\mathcal{B}^*$ conforming to the Frozen Schema and accurately capturing the true side effects of repository code, the policy engine $g$ deterministically maps $(\mathcal{B}^*, p_{\text{intent}})$ to a unique decision.

Formally, for any two implementations $\theta_1, \theta_2$ of Layer 2, if they produce the same behaviors:
$$f_{\theta_1}(R) = f_{\theta_2}(R) = \mathcal{B}^*$$

Then they produce the same decision:
$$g(f_{\theta_1}(R), p_{\text{intent}}) = g(f_{\theta_2}(R), p_{\text{intent}})$$

**Justification:**

The decision function $g$ is deterministic and depends only on $\mathcal{B}^*$ and $p_{\text{intent}}$, not on the implementation $\theta$. Therefore, identical behaviors lead to identical decisions.

**Practical Considerations:**

In practice, extractors have extraction errors. We control this through:
1. **Hard test sets:** Regression tests (Hard-3/10/13/16) ensure prompt changes don't break extraction
2. **Gold vs E2E alignment:** Comparing gold-labeled behaviors with LLM-extracted behaviors (Acc_L2 metric)
3. **Rule-based baseline:** Empirical validation showing 86.7% decision agreement despite different extraction accuracy

**Empirical Validation:**

| Implementation | ASR | FBR | Decision Agreement |
|----------------|-----|-----|--------------------|
| LLM-based (v4.1) | 0.0% | 3.3% | - |
| Rule-based | 26.7% | 3.3% | 86.7% (52/60) |

**Interpretation:**

The architecture (Frozen Schema + Deterministic Policy) is implementation-agnostic. Different implementations may have different extraction accuracy, but the policy engine produces consistent decisions given the same behaviors.

The identical FBR (3.3%) across both implementations confirms policy engine consistency.

---

## 5. Coverage Analysis

### 5.1 Theoretical Coverage

**Full Threat Space:**
$$|\mathcal{T}| = 4 \times 5 \times 5 = 100 \text{ combinations}$$

**SemiReal-60 v2 Coverage:**

**By Carrier:**
- METADATA: 18 cases (30%)
- DOCS: 6 cases (10%)
- SOURCE: 18 cases (30%)
- BUILD: 18 cases (30%)

**By Lifecycle:**
- SETUP: 18 cases (30%)
- PLANNING: 6 cases (10%)
- CODING: 6 cases (10%)
- EXECUTION: 18 cases (30%)
- PUBLISH: 12 cases (20%)

**By Privilege:**
- L0: 6 cases (10%)
- L1: 6 cases (10%)
- L2: 12 cases (20%)
- L3: 18 cases (30%)
- L4: 18 cases (30%)

**High-Risk Focus:**

The benchmark prioritizes high-risk combinations:
- EXECUTION × L3/L4: 12 cases
- PUBLISH × L3/L4: 8 cases
- BUILD × L3/L4: 10 cases

**Rationale:**

Not all 100 combinations are equally important. Low-risk combinations (e.g., PLANNING × L0) are less critical for security evaluation. The benchmark focuses on combinations where attacks are most likely and most damaging.

### 5.2 Obfuscation Coverage

**Obfuscation Types:**
- NONE: 24 cases (40%)
- TARGET_HIDING: 18 cases (30%)
- PAYLOAD_HIDING: 12 cases (20%)
- CONTENT_DATA: 6 cases (10%)

**Cross-Cutting Concern:**

Obfuscation is orthogonal to C-L-P, creating additional test dimensions.

---

## 6. Comparison with Baselines

### 6.1 LLM Judge

**Function:**
$$h_{\text{LLM}}: R \times \tau \rightarrow \{\text{ALLOW}, \text{BLOCK}\}$$

**Problem:**
- No structured evidence ($\mathcal{B}^*$ is implicit)
- No explicit policy rules
- Non-deterministic (temperature > 0)

**Result:**
- ASR = 0.0% (same as CodeGuard)
- FBR = 36.7% (11× worse than CodeGuard)

### 6.2 SAST

**Function:**
$$h_{\text{SAST}}: R \rightarrow \{\text{ALLOW}, \text{BLOCK}\}$$

**Problem:**
- Pattern matching only (no semantic understanding)
- No data flow analysis
- Brittle to obfuscation

**Result:**
- ASR = 6.7% (misses 2/30 attacks)
- FBR = 30.0% (9× worse than CodeGuard)

### 6.3 CodeGuard Advantage

**Structured Evidence + Deterministic Policy:**
$$\text{CodeGuard} = f_\theta(R) \rightarrow \mathcal{B}^* \xrightarrow{g} \{\text{ALLOW}, \text{BLOCK}\}$$

**Result:**
- ASR = 0.0% (perfect security)
- FBR = 3.3% (low false positives)
- Utility = 98.3% (best overall)

**Key Insight:**

The separation of evidence extraction (Layer 2) and decision making (Layer 3) enables both high accuracy and full auditability.

---

## 7. Summary

**Core Formalization:**
1. Threat space: $\mathcal{T} = \mathcal{C} \times \mathcal{L} \times \mathcal{P}$ (100 combinations)
2. Layer 2: $f_\theta: R \rightarrow \mathcal{B}^*$ (evidence extraction)
3. Layer 3: $g: \mathcal{B}^* \times \mathcal{P} \rightarrow \{\text{ALLOW}, \text{BLOCK}\}$ (deterministic policy)
4. Metrics: ASR, FBR, Utility (well-defined, reproducible)

**Key Properties:**
- Implementation-agnostic architecture
- Deterministic policy (auditability)
- Structured evidence (traceability)
- Comprehensive coverage (60 cases, high-risk focus)

**Empirical Validation:**
- CodeGuard: ASR=0.0%, FBR=3.3%, Utility=98.3%
- Significantly outperforms LLM Judge (FBR 11×) and SAST (FBR 9×, ASR 6.7%)

---

**This formalization provides the mathematical rigor needed for a top-tier venue while remaining accessible and grounded in the empirical results.**
