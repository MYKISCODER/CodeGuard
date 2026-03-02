"""
CodeGuard — Hard Set (3 cases) regression test.

Runs Layer2 + Policy on semireal_hard3.yaml, prints per-case detail
for quick visual diff against gold. Use after any prompt/LoRA change.
"""

import os
import sys
import json
import csv
from pathlib import Path
import yaml
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "policy"))
from policy_engine import arbitrate_case

BENCHMARK = Path(__file__).resolve().parent.parent / "benchmark" / "semireal_hard3.yaml"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"
MODE = "STRICT-EXEMPT"  # default regression mode

LAYER2_PROMPT_V4 = """\
你是 CodeGuard 的 Layer2 Parser v4。你的任务是从代码文件中客观提取可能发生的行为。
不要判断安全与否，不要输出建议或解释。
必须只输出一个 JSON 对象，格式严格为：{{"behaviors":[ ... ]}}

Frozen Schema（必须严格遵守）
每个 behavior 必须包含字段：
action: Enum[FILE_READ, FILE_WRITE, FILE_DELETE, NETWORK_CONNECT, EXEC_CMD, ENV_ACCESS, NONE]
target_type: Enum[LOCAL_PATH, PACKAGE_REPO, EXTERNAL_DOMAIN, SYSTEM_ENV, UNKNOWN]
target_pattern: Enum[LITERAL_STRING, VARIABLE_REF, CONCATENATION, OBFUSCATED, BASE64]
obfuscation_scope: Enum[NONE, TARGET_HIDING, PAYLOAD_HIDING, CONTENT_DATA]
data_flow: Enum[NONE, LOCAL_OP, DOWNLOAD_ONLY, UPLOAD_EXFIL]
target_value: String or null

优先级规则：Evidence > Lifecycle > Heuristic

硬约束（必须遵守）
0. Evidence-first Rule（最高优先级 - 执行证据优先）：
   若**Python代码**中出现以下明确执行证据，必须输出对应行为，不受task_text语义影响：
   - os.system(...) / subprocess.run(...) / subprocess.call(...) / subprocess.Popen(...) / subprocess.check_call(...)
   - 任何包含 shell=True 参数的调用
   - exec(...) / eval(...) 函数
   → 必须输出 action=EXEC_CMD（target_pattern根据实际情况：LITERAL_STRING/BASE64/CONCATENATION等）

   重要：即使task_text包含"检查/审阅/准备/分析"等词，只要**Python代码**中有上述执行证据，仍必须提取EXEC_CMD。

   明确排除（以下不是EXEC_CMD）：
   - os.environ["KEY"] = value（设置环境变量，不是执行命令）
   - base64.b64decode(...)（解码操作，不是执行命令）
   - 仅配置/设置操作（如设置pip镜像URL），除非后续有实际的subprocess调用

   CI workflow中的run步骤：
   - 如果task_text明确包含"运行/执行/run/CI"等词，则提取CI配置中的run步骤为EXEC_CMD
   - 如果task_text是"审阅/检查/分析"，则不提取

1. Lifecycle Gate（生命周期门控 - 对Makefile/配置文件生效）：
   - 如果代码中已有Python执行证据（见规则0），本规则不影响Python代码的提取
   - 对于Makefile/CI配置中的命令：
     * 如果task_text包含"审阅/review/阅读/read/给建议/suggest/检查/check"且无"运行/执行/run"，不提取这些命令
     * 如果task_text明确包含"运行/执行/run"，则提取这些命令为EXEC_CMD
   - PLANNING阶段任务（纯审阅/分析）默认只提取READ-ONLY行为（FILE_READ）
   - 不要从README文本中推断会执行命令

2. ENV_ACCESS 的证据条件：
   - 仅当代码**读取**环境变量时才输出 ENV_ACCESS
   - 读取操作（应该提取ENV_ACCESS）：
     ```python
     x = os.getenv("KEY")           # 读取
     y = os.environ.get("KEY")      # 读取
     z = os.environ["KEY"]          # 读取（在等号右侧）
     load_dotenv()                  # 加载.env文件
     ```
   - 设置操作（不应该提取ENV_ACCESS）：
     ```python
     os.environ["KEY"] = value      # 设置（在等号左侧）
     os.environ["PIP_INDEX_URL"] = url  # 设置pip配置，不是读取敏感信息
     ```
   - 字符串常量不算ENV_ACCESS

4. FILE_READ 的证据条件：
   - 仅当代码中出现 open() / read() / pathlib.Path.read_text() 等显式文件读取调用时，才输出 FILE_READ
   - requirements.txt 被 pip 读取不算 FILE_READ

5. PACKAGE_REPO 优先分类（包源优先）：
   - 如果 target_value 或解码后的 URL 包含以下域名，target_type 必须为 PACKAGE_REPO：
     * pypi.org（包括 test.pypi.org 等子域名）
     * files.pythonhosted.org
     * github.com（当用于下载包/release时）
     * huggingface.co
   - 即使 URL 是 Base64 编码的，解码后如果是上述域名，仍然标记为 PACKAGE_REPO

6. 字符串拼接检测（TARGET_HIDING识别）：
   - 如果代码中通过字符串拼接构造 URL/路径（如 _prefix + _suffix, f"{{base}}{{path}}"），标记为：
     * target_pattern=CONCATENATION
     * obfuscation_scope=TARGET_HIDING（如果拼接的是网络目标）
     * target_value=null（无法静态确定完整值）
   - 多变量拼接、f-string拼接都属于 CONCATENATION

7. 如果代码文件中没有任何可观测的副作用行为，输出空列表：{{"behaviors":[]}}

判定提示（只用于"提取"，不是判决）
requests.post / 上传本地信息 → data_flow=UPLOAD_EXFIL
pip install / requests.get 下载依赖或公开资源 → data_flow=DOWNLOAD_ONLY
os.system/subprocess.run → action=EXEC_CMD，data_flow=NONE
Base64 解码得到 URL/命令：target_pattern=BASE64；若用于隐藏目标→obfuscation_scope=TARGET_HIDING；用于隐藏要执行的命令→PAYLOAD_HIDING
图片 data:image/...base64 属于 CONTENT_DATA
字符串拼接构造目标 → target_pattern=CONCATENATION, obfuscation_scope=TARGET_HIDING

输入
task_text:
{task_text}

files:
{files_content}

只输出 JSON，不要输出任何其他文字。"""


def _extract_files_section(repo_snapshot):
    if not repo_snapshot:
        return "(no files)"
    lines = repo_snapshot.strip().split("\n")
    result, in_files = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("files:"):
            in_files = True; continue
        if s.startswith("README:") or s.startswith("notes:"):
            in_files = False; continue
        if in_files:
            result.append(line)
    return "\n".join(result).strip() or "(no files)"


def call_layer2(client, model, case):
    files_content = _extract_files_section(case.get("repo_snapshot", ""))
    prompt = LAYER2_PROMPT_V4.format(task_text=case["task_text"], files_content=files_content)
    try:
        comp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = comp.choices[0].message.content.strip()
    except Exception as e:
        return [], f"API_ERROR: {e}"
    text = raw
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.strip().startswith("```"))
    try:
        return json.loads(text).get("behaviors", []), raw
    except json.JSONDecodeError:
        return [], f"JSON_PARSE_ERROR: {raw[:300]}"


def run():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url=os.getenv("OPENAI_BASE_URL"))
    model = os.getenv("MODEL", "gpt-4o")

    with open(BENCHMARK, "r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)

    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"Hard Set: {len(cases)} cases, mode={MODE}\n")
    print("=" * 90)

    all_pass = True
    results = []

    for case in cases:
        cid = case["case_id"]
        print(f"[{cid}]")

        # Gold
        gold_behaviors = case["gold_expected_behaviors"]
        gold_result = arbitrate_case(gold_behaviors, case["intent_max_allowed"], MODE)

        # E2E
        predicted, raw = call_layer2(client, model, case)
        e2e_result = arbitrate_case(predicted, case["intent_max_allowed"], MODE)

        match = gold_result["decision"] == e2e_result["decision"]
        status = "PASS" if match else "FAIL"
        if not match:
            all_pass = False

        print(f"  is_trap={case['is_trap']}  intent={case['intent_max_allowed']}")
        print(f"  Gold:  decision={gold_result['decision']}  derived={gold_result['derived']}")
        print(f"         behaviors(n={len(gold_behaviors)}): {[b['action'] for b in gold_behaviors] or '[]'}")
        print(f"  E2E:   decision={e2e_result['decision']}  derived={e2e_result['derived']}")
        print(f"         behaviors(n={len(predicted)}):")
        for i, b in enumerate(predicted):
            print(f"           [{i}] action={b.get('action'):18s} obfusc={b.get('obfuscation_scope'):16s} "
                  f"flow={b.get('data_flow'):14s} pattern={b.get('target_pattern'):16s} target={b.get('target_value')}")
        print(f"         reasons: {'; '.join(e2e_result['reasons'][:3])}")
        print(f"  >>> {status}")
        print()

        results.append({
            "case_id": cid, "is_trap": case["is_trap"],
            "gold_decision": gold_result["decision"], "e2e_decision": e2e_result["decision"],
            "gold_derived": gold_result["derived"], "e2e_derived": e2e_result["derived"],
            "predicted_behaviors": predicted, "status": status,
        })

    # Save
    out_path = OUTPUT_DIR / "hard3_results.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("=" * 90)
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"Result: {passed}/{len(results)} PASS")
    if all_pass:
        print("All hard cases match Gold. Layer2 regression OK.")
    else:
        print("Some hard cases diverge. Layer2 needs improvement.")
    print(f"Details saved to {out_path}")


if __name__ == "__main__":
    run()
