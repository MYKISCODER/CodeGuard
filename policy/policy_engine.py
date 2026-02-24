"""
CodeGuard Layer 3 — Deterministic Policy Engine (Frozen Spec)

Implements privilege mapping, allowlist, obfuscation penalty,
unresolvable-target escalation, and final ALLOW/BLOCK decision.
"""

from urllib.parse import urlparse
import fnmatch

# ── Integer privilege ranking (spec §5.4) ──────────────────────────
PRIV_RANK = {"L0": 0, "L1": 1, "L2": 2, "L3": 3, "L4": 4}
RANK_TO_LABEL = {v: k for k, v in PRIV_RANK.items()}

# ── Sensitive paths (spec §5.1, MVP minimal set) ───────────────────
SENSITIVE_PREFIXES = [
    ".env", ".ssh/", "/etc/passwd", "/etc/shadow",
    "~/.aws/", "~/.gitconfig",
]
SENSITIVE_GLOBS = ["**/credentials*", "**/secrets*", "**/*token*"]


def _is_sensitive(path):
    if not path:
        return False
    p = path.strip()
    for prefix in SENSITIVE_PREFIXES:
        if p == prefix or p.startswith(prefix):
            return True
    for pattern in SENSITIVE_GLOBS:
        if fnmatch.fnmatch(p, pattern):
            return True
    return False


# ── Allowlist (spec §5.2) ──────────────────────────────────────────
SAFE_HOSTS = {
    "pypi.org", "github.com", "huggingface.co", "files.pythonhosted.org"
}


def _host_in_allowlist(target_value):
    if not target_value:
        return False
    url = target_value if "://" in target_value else f"http://{target_value}"
    try:
        hostname = urlparse(url).hostname
        if not hostname:
            return False
        hostname = hostname.lower()
        if hostname in SAFE_HOSTS:
            return True
        return any(hostname.endswith("." + h) for h in SAFE_HOSTS)
    except Exception:
        return False


# ── Privilege mapping (spec §5.1) ──────────────────────────────────
# Priority: R1 > R3 > R6 > R5 > R4b > R4 > R4c > R2b > R2 > R7
def _base_privilege(behavior):
    """Return (privilege_label, rule_id) for one behavior."""
    action = behavior.get("action", "NONE")
    target_type = behavior.get("target_type", "UNKNOWN")
    data_flow = behavior.get("data_flow", "NONE")
    target_value = behavior.get("target_value")

    # R1
    if data_flow == "UPLOAD_EXFIL":
        return "L3", "R1"
    # R3
    if action == "EXEC_CMD":
        return "L4", "R3"
    # R6
    if action == "ENV_ACCESS":
        return "L3", "R6"
    # R5 / R5b
    if action == "FILE_READ":
        if _is_sensitive(target_value):
            return "L3", "R5"
        return "L1", "R5b"
    # R4b / R4c
    if action == "FILE_DELETE":
        if _is_sensitive(target_value):
            return "L4", "R4b"
        return "L2", "R4c"
    # R4
    if action == "FILE_WRITE":
        return "L2", "R4"
    # R2b
    if data_flow == "DOWNLOAD_ONLY" and target_type in ("EXTERNAL_DOMAIN", "UNKNOWN"):
        return "L2", "R2b"
    # R2
    if data_flow == "DOWNLOAD_ONLY" and target_type == "PACKAGE_REPO":
        return "L2", "R2"
    # R7
    return "L1", "R7"


# ── Single-behavior arbitration ────────────────────────────────────
def arbitrate_behavior(behavior, intent_max_allowed, mode="STRICT"):
    """
    Evaluate ONE behavior against the frozen policy.

    Returns dict: decision, derived, rule, reason
    """
    mode = mode.upper()
    priv_label, rule = _base_privilege(behavior)
    priv = PRIV_RANK[priv_label]
    reason_parts = [f"base={priv_label}({rule})"]

    action = behavior.get("action", "NONE")
    target_type = behavior.get("target_type", "UNKNOWN")
    target_pattern = behavior.get("target_pattern", "LITERAL_STRING")
    obfuscation = behavior.get("obfuscation_scope", "NONE")
    data_flow = behavior.get("data_flow", "NONE")
    target_value = behavior.get("target_value")

    # §5.3 Obfuscation penalty
    if obfuscation in ("TARGET_HIDING", "PAYLOAD_HIDING"):
        if mode == "STRICT":
            return {
                "decision": "BLOCK",
                "derived": priv_label,
                "rule": rule,
                "reason": f"{reason_parts[0]}; obfusc={obfuscation}->BLOCK(STRICT)",
            }
        elif mode == "STRICT-EXEMPT":
            # Narrow exemption: allow obfuscated package-source downloads
            # to proceed to allowlist check instead of immediate BLOCK
            if data_flow == "DOWNLOAD_ONLY" and target_type == "PACKAGE_REPO":
                reason_parts.append(f"obfusc={obfuscation}->EXEMPT(DOWNLOAD+PKG)")
            else:
                return {
                    "decision": "BLOCK",
                    "derived": priv_label,
                    "rule": rule,
                    "reason": f"{reason_parts[0]}; obfusc={obfuscation}->BLOCK(STRICT-EXEMPT)",
                }
        elif mode == "MODERATE":
            priv = max(priv, PRIV_RANK["L4"])
            priv_label = RANK_TO_LABEL[priv]
            reason_parts.append(f"obfusc={obfuscation}->L4(MODERATE)")
        else:
            reason_parts.append(f"obfusc={obfuscation}->log(PERMISSIVE)")

    # §5.2 Allowlist exemption
    if (rule == "R2"
            and target_type == "PACKAGE_REPO"
            and data_flow == "DOWNLOAD_ONLY"
            and target_pattern == "LITERAL_STRING"
            and _host_in_allowlist(target_value)):
        priv = PRIV_RANK["L1"]
        priv_label = "L1"
        reason_parts.append("allowlist->L1")

    # §5.3b Unresolvable target escalation
    if (action in ("FILE_READ", "FILE_DELETE")
            and target_pattern != "LITERAL_STRING"
            and target_value is None):
        if mode in ("STRICT", "MODERATE"):
            new_priv = min(priv + 1, PRIV_RANK["L4"])
            if new_priv != priv:
                priv = new_priv
                priv_label = RANK_TO_LABEL[priv]
                reason_parts.append(f"unresolvable_target->+1->{priv_label}")
        else:
            reason_parts.append("unresolvable_target->log(PERMISSIVE)")

    # §5.4 Final decision
    allowed_rank = PRIV_RANK.get(intent_max_allowed, 0)
    decision = "BLOCK" if priv > allowed_rank else "ALLOW"
    reason_parts.append(f"derived={priv_label} vs intent={intent_max_allowed}->{decision}")

    return {
        "decision": decision,
        "derived": priv_label,
        "rule": rule,
        "reason": "; ".join(reason_parts),
    }


# ── Case-level arbitration (OR rule) ──────────────────────────────
def arbitrate_case(behaviors, intent_max_allowed, mode="STRICT"):
    """
    Evaluate a full case (list of behaviors).
    OR rule: any BLOCK -> case BLOCK.
    """
    if not behaviors:
        return {"decision": "ALLOW", "derived": "L0", "reasons": ["no behaviors"]}

    results = [arbitrate_behavior(b, intent_max_allowed, mode) for b in behaviors]

    case_decision = "BLOCK" if any(r["decision"] == "BLOCK" for r in results) else "ALLOW"
    case_derived = RANK_TO_LABEL[max(PRIV_RANK[r["derived"]] for r in results)]
    reasons = [r["reason"] for r in results]

    return {"decision": case_decision, "derived": case_derived, "reasons": reasons}
