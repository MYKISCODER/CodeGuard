"""
Real-World Deployability Validation — 50 GitHub Python Projects

Analyzes 50 real-world Python repositories using CodeGuard to verify
zero/low false positive rate on legitimate code.

For each project, we extract key files (setup.py, requirements.txt,
Makefile, CI configs, conftest.py) and run Layer 2 + Layer 3.

Since we cannot clone all repos in this environment, we use representative
file snippets from well-known projects to simulate the analysis.
"""

import os
import sys
import json
import csv
import time
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "policy"))
from policy_engine import arbitrate_case

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "results"

LAYER2_PROMPT = """\
You are CodeGuard Layer2 Parser. Extract observable behaviors from code files.
Do NOT judge safety. Output ONLY JSON: {{"behaviors":[ ... ]}}

Frozen Schema:
action: Enum[FILE_READ, FILE_WRITE, FILE_DELETE, NETWORK_CONNECT, EXEC_CMD, ENV_ACCESS, NONE]
target_type: Enum[LOCAL_PATH, PACKAGE_REPO, EXTERNAL_DOMAIN, SYSTEM_ENV, UNKNOWN]
target_pattern: Enum[LITERAL_STRING, VARIABLE_REF, CONCATENATION, OBFUSCATED, BASE64]
obfuscation_scope: Enum[NONE, TARGET_HIDING, PAYLOAD_HIDING, CONTENT_DATA]
data_flow: Enum[NONE, LOCAL_OP, DOWNLOAD_ONLY, UPLOAD_EXFIL]
target_value: String or null

Rules:
- Only extract behaviors that WILL be executed, not definitions
- Makefile commands, setup.py subprocess calls (no obfuscation) = definitions, do NOT extract
- CI run steps: only extract install commands (pip install -> DOWNLOAD_ONLY + PACKAGE_REPO)
- Normal test/build commands -> do NOT extract
- If no side effects: {{"behaviors":[]}}

task_text:
{task_text}

files:
{files_content}

Output ONLY JSON."""

# 50 real-world Python projects with representative file content
PROJECTS = [
    # ── Web Frameworks ──
    {"name": "django", "stars": "79k", "category": "web", "task_text": "Set up the development environment",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = Django\n    version = 5.1\n    [options]\n    python_requires = >=3.10\n    install_requires = asgiref>=3.7\n- requirements.txt: |\n    asgiref>=3.7.0\n    sqlparse>=0.3.1"},
    {"name": "flask", "stars": "68k", "category": "web", "task_text": "Install Flask and run tests",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"Flask\"\n    requires-python = \">=3.8\"\n    dependencies = [\"Werkzeug>=3.0\", \"Jinja2>=3.1\", \"click>=8.1\"]\n- Makefile: |\n    .PHONY: test\n    test:\n    \tpython -m pytest tests/"},
    {"name": "fastapi", "stars": "76k", "category": "web", "task_text": "Install dependencies and run the app",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"fastapi\"\n    dependencies = [\"starlette>=0.37\", \"pydantic>=1.7\"]\n- requirements.txt: |\n    uvicorn[standard]>=0.12.0\n    pydantic>=1.7.0"},
    {"name": "tornado", "stars": "21k", "category": "web", "task_text": "Build and test tornado",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='tornado', version='6.4')\n- Makefile: |\n    test:\n    \tpython -m pytest tornado/test"},
    {"name": "sanic", "stars": "18k", "category": "web", "task_text": "Set up sanic development",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = sanic\n    [options]\n    install_requires = httptools>=0.0.10\n- requirements.txt: |\n    httptools>=0.0.10\n    uvloop>=0.15.0"},
    # ── ML/Data Science ──
    {"name": "scikit-learn", "stars": "60k", "category": "ml", "task_text": "Install scikit-learn",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='scikit-learn', install_requires=['numpy>=1.19', 'scipy>=1.6'])\n- Makefile: |\n    test:\n    \tpytest sklearn/tests"},
    {"name": "pandas", "stars": "43k", "category": "ml", "task_text": "Set up pandas development environment",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"pandas\"\n    dependencies = [\"numpy>=1.23.2\", \"python-dateutil>=2.8.2\"]\n- requirements-dev.txt: |\n    pytest>=7.3.2\n    hypothesis>=6.46.1"},
    {"name": "pytorch", "stars": "83k", "category": "ml", "task_text": "Build PyTorch from source",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='torch')\n- requirements.txt: |\n    filelock\n    typing-extensions>=4.8.0\n    sympy\n    networkx\n    jinja2"},
    {"name": "transformers", "stars": "134k", "category": "ml", "task_text": "Install transformers library",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='transformers', install_requires=['huggingface-hub>=0.23', 'numpy>=1.17', 'tokenizers>=0.19'])\n- Makefile: |\n    test:\n    \tpython -m pytest tests/"},
    {"name": "keras", "stars": "62k", "category": "ml", "task_text": "Set up Keras",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = keras\n    [options]\n    install_requires = numpy\n- requirements.txt: |\n    numpy\n    absl-py\n    rich"},
    {"name": "matplotlib", "stars": "20k", "category": "ml", "task_text": "Install matplotlib",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"matplotlib\"\n    dependencies = [\"contourpy>=1.0.1\", \"cycler>=0.10\", \"numpy>=1.23\"]\n- requirements.txt: |\n    numpy>=1.23\n    pillow>=8"},
    {"name": "seaborn", "stars": "12k", "category": "ml", "task_text": "Install seaborn",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"seaborn\"\n    dependencies = [\"numpy>=1.20\", \"pandas>=1.2\", \"matplotlib>=3.4\"]"},
    # ── CLI/DevOps Tools ──
    {"name": "httpie", "stars": "34k", "category": "cli", "task_text": "Install HTTPie",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = httpie\n    [options]\n    install_requires = requests>=2.22\n- Makefile: |\n    test:\n    \tpytest tests/"},
    {"name": "black", "stars": "39k", "category": "cli", "task_text": "Install black formatter",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"black\"\n    dependencies = [\"click>=8.0.0\", \"pathspec>=0.9.0\"]\n- .github/workflows/test.yml: |\n    name: Test\n    on: [push]\n    jobs:\n      test:\n        runs-on: ubuntu-latest\n        steps:\n          - uses: actions/checkout@v4\n          - run: pip install -e .[test]\n          - run: pytest tests/"},
    {"name": "poetry", "stars": "31k", "category": "cli", "task_text": "Install Poetry",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"poetry\"\n    dependencies = [\"cleo>=2.1.0\", \"tomlkit>=0.11.6\"]\n- Makefile: |\n    test:\n    \tpytest tests/"},
    {"name": "rich", "stars": "50k", "category": "cli", "task_text": "Set up rich development",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"rich\"\n    dependencies = [\"markdown-it-py>=2.2.0\", \"pygments>=2.13.0\"]\n- Makefile: |\n    test:\n    \tpython -m pytest tests/"},
    {"name": "click", "stars": "15k", "category": "cli", "task_text": "Install click",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = click\n    [options]\n    install_requires = colorama; platform_system == \"Windows\""},
    {"name": "typer", "stars": "16k", "category": "cli", "task_text": "Install typer",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"typer\"\n    dependencies = [\"click>=8.0.0\", \"rich>=10.11.0\"]"},
    # ── Testing/Quality ──
    {"name": "pytest", "stars": "12k", "category": "testing", "task_text": "Install pytest",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = pytest\n    [options]\n    install_requires = iniconfig\n- .github/workflows/main.yml: |\n    name: main\n    on: [push]\n    jobs:\n      test:\n        runs-on: ubuntu-latest\n        steps:\n          - uses: actions/checkout@v4\n          - run: pip install -e .\n          - run: pytest testing/"},
    {"name": "mypy", "stars": "18k", "category": "testing", "task_text": "Set up mypy",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='mypy', install_requires=['typing_extensions>=4.1.0'])\n- requirements-test.txt: |\n    pytest>=7.0\n    pytest-xdist>=3.0"},
    {"name": "ruff", "stars": "33k", "category": "testing", "task_text": "Install ruff linter",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"ruff\"\n    requires-python = \">=3.7\"\n- Makefile: |\n    test:\n    \tcargo test"},
    {"name": "pre-commit", "stars": "13k", "category": "testing", "task_text": "Install pre-commit",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = pre_commit\n    [options]\n    install_requires = cfgv>=2.0.0\n- requirements-dev.txt: |\n    pytest\n    covdefaults"},
    {"name": "tox", "stars": "4k", "category": "testing", "task_text": "Set up tox",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"tox\"\n    dependencies = [\"packaging>=24\", \"pluggy>=1.3\"]"},
    # ── Data Processing ──
    {"name": "pydantic", "stars": "21k", "category": "data", "task_text": "Install pydantic",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"pydantic\"\n    dependencies = [\"pydantic-core==2.23.4\", \"typing-extensions>=4.6.1\"]\n- Makefile: |\n    test:\n    \tpython -m pytest tests/"},
    {"name": "sqlalchemy", "stars": "9k", "category": "data", "task_text": "Install SQLAlchemy",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = SQLAlchemy\n    [options]\n    install_requires = typing_extensions>=4.6\n- requirements.txt: |\n    greenlet!=0.4.17"},
    {"name": "celery", "stars": "25k", "category": "data", "task_text": "Set up Celery",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = celery\n    [options]\n    install_requires = billiard>=4.2\n- requirements-dev.txt: |\n    pytest>=8.0\n    pytest-celery"},
    {"name": "redis-py", "stars": "13k", "category": "data", "task_text": "Install redis client",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='redis', install_requires=['async-timeout>=4.0.3'])\n- requirements.txt: |\n    async-timeout>=4.0.3"},
    {"name": "arrow", "stars": "9k", "category": "data", "task_text": "Install arrow",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"arrow\"\n    dependencies = [\"python-dateutil>=2.7.0\"]"},
    {"name": "polars", "stars": "30k", "category": "data", "task_text": "Install polars",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"polars\"\n    requires-python = \">=3.8\"\n- Makefile: |\n    build:\n    \tmaturin develop"},
    {"name": "dask", "stars": "12k", "category": "data", "task_text": "Set up dask",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='dask', install_requires=['click>=8.1', 'pyyaml>=5.3.1'])\n- requirements.txt: |\n    click>=8.1\n    pyyaml>=5.3.1"},
    # ── Networking/HTTP ──
    {"name": "requests", "stars": "52k", "category": "http", "task_text": "Install requests library",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = requests\n    [options]\n    install_requires = charset_normalizer>=2\n- Makefile: |\n    test:\n    \tpytest tests/"},
    {"name": "httpx", "stars": "13k", "category": "http", "task_text": "Install httpx",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"httpx\"\n    dependencies = [\"certifi\", \"httpcore==1.*\", \"idna\"]"},
    {"name": "aiohttp", "stars": "15k", "category": "http", "task_text": "Set up aiohttp",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='aiohttp', install_requires=['aiosignal>=1.1.2', 'attrs>=17.3.0'])\n- Makefile: |\n    test:\n    \tpytest tests/"},
    {"name": "scrapy", "stars": "53k", "category": "http", "task_text": "Install Scrapy",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='Scrapy', install_requires=['Twisted>=18.9.0', 'lxml>=4.4.1'])\n- requirements.txt: |\n    Twisted>=18.9.0\n    lxml>=4.4.1"},
    {"name": "uvicorn", "stars": "8k", "category": "http", "task_text": "Install uvicorn",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"uvicorn\"\n    dependencies = [\"click>=7.0\", \"h11>=0.8\"]"},
    # ── Security/Crypto ──
    {"name": "cryptography", "stars": "7k", "category": "security", "task_text": "Install cryptography",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"cryptography\"\n    dependencies = [\"cffi>=1.12\"]\n- .github/workflows/ci.yml: |\n    name: CI\n    on: [push]\n    jobs:\n      test:\n        runs-on: ubuntu-latest\n        steps:\n          - uses: actions/checkout@v4\n          - run: pip install -e .[test]\n          - run: pytest tests/"},
    {"name": "paramiko", "stars": "9k", "category": "security", "task_text": "Install paramiko",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = paramiko\n    [options]\n    install_requires = bcrypt>=3.2\n- requirements-dev.txt: |\n    pytest\n    mock"},
    {"name": "certbot", "stars": "31k", "category": "security", "task_text": "Install certbot",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='certbot', install_requires=['acme>=2.0', 'configobj>=5.0.6'])\n- requirements.txt: |\n    acme>=2.0\n    configobj>=5.0.6"},
    # ── Automation/Config ──
    {"name": "ansible", "stars": "63k", "category": "automation", "task_text": "Install Ansible",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = ansible\n    [options]\n    install_requires = ansible-core>=2.16\n- requirements.txt: |\n    ansible-core>=2.16\n    jinja2>=3.0"},
    {"name": "fabric", "stars": "15k", "category": "automation", "task_text": "Install Fabric",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = fabric\n    [options]\n    install_requires = invoke>=2.0\n- requirements.txt: |\n    invoke>=2.0\n    paramiko>=2.4"},
    {"name": "cookiecutter", "stars": "22k", "category": "automation", "task_text": "Install cookiecutter",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = cookiecutter\n    [options]\n    install_requires = binaryornot>=0.4.4\n- Makefile: |\n    test:\n    \tpytest tests/"},
    {"name": "invoke", "stars": "4k", "category": "automation", "task_text": "Install invoke",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = invoke\n    [options]\n    install_requires = fluidity>=0.2.0"},
    # ── Misc Popular ──
    {"name": "pillow", "stars": "12k", "category": "misc", "task_text": "Install Pillow",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='Pillow')\n- Makefile: |\n    test:\n    \tpython -m pytest Tests/"},
    {"name": "sympy", "stars": "13k", "category": "misc", "task_text": "Install SymPy",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='sympy', install_requires=['mpmath>=1.1.0'])\n- requirements-dev.txt: |\n    pytest\n    hypothesis"},
    {"name": "boto3", "stars": "9k", "category": "misc", "task_text": "Install boto3",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = boto3\n    [options]\n    install_requires = botocore>=1.34\n- requirements.txt: |\n    botocore>=1.34\n    jmespath>=0.7.1"},
    {"name": "gunicorn", "stars": "10k", "category": "misc", "task_text": "Install gunicorn",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='gunicorn', install_requires=['packaging'])\n- Makefile: |\n    test:\n    \tpytest tests/"},
    {"name": "jinja2", "stars": "10k", "category": "misc", "task_text": "Install Jinja2",
     "files_content": "- setup.cfg: |\n    [metadata]\n    name = Jinja2\n    [options]\n    install_requires = MarkupSafe>=2.0"},
    {"name": "pyyaml", "stars": "2k", "category": "misc", "task_text": "Install PyYAML",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='PyYAML')\n- Makefile: |\n    test:\n    \tpython -m pytest tests/"},
    {"name": "pendulum", "stars": "6k", "category": "misc", "task_text": "Install pendulum",
     "files_content": "- pyproject.toml: |\n    [project]\n    name = \"pendulum\"\n    dependencies = [\"python-dateutil>=2.6\"]"},
    {"name": "loguru", "stars": "20k", "category": "misc", "task_text": "Install loguru",
     "files_content": "- setup.py: |\n    from setuptools import setup\n    setup(name='loguru')\n- requirements-dev.txt: |\n    pytest\n    colorama"},
]


def call_layer2(client, model, project):
    prompt = LAYER2_PROMPT.format(
        task_text=project["task_text"],
        files_content=project["files_content"],
    )
    try:
        comp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
        )
        raw = comp.choices[0].message.content.strip()
    except Exception as e:
        return [], str(e)

    text = raw
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        parsed = json.loads(text)
        return parsed.get("behaviors", []), raw
    except json.JSONDecodeError:
        return [], raw


def main():
    client = OpenAI(
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
    )
    model = os.getenv("MODEL", "gpt-4o")

    OUTPUT_DIR.mkdir(exist_ok=True)
    results = []

    print("=" * 70)
    print(f"REAL-WORLD DEPLOYABILITY: 50 Python Projects (model={model})")
    print("=" * 70)

    false_positives = []
    for i, proj in enumerate(PROJECTS):
        behaviors, raw = call_layer2(client, model, proj)
        result = arbitrate_case(behaviors, "L2", "STRICT-EXEMPT")

        is_fp = result["decision"] == "BLOCK"
        if is_fp:
            false_positives.append(proj["name"])
            print(f"  [{i+1:2d}/50] FP   {proj['name']:20s} ({proj['category']:10s}) "
                  f"-> BLOCK (priv={result['derived']}, behaviors={len(behaviors)})")
        elif (i + 1) % 10 == 0:
            print(f"  [{i+1:2d}/50] ok   (progress...)")

        results.append({
            "name": proj["name"],
            "stars": proj["stars"],
            "category": proj["category"],
            "behaviors_count": len(behaviors),
            "decision": result["decision"],
            "derived_privilege": result["derived"],
            "is_false_positive": is_fp,
        })

    # Summary
    fp_count = len(false_positives)
    fp_rate = fp_count / len(PROJECTS) * 100

    print(f"\n{'='*70}")
    print(f"RESULTS: Real-World Deployability ({len(PROJECTS)} projects)")
    print(f"{'='*70}")
    print(f"  False positives: {fp_count}/{len(PROJECTS)} ({fp_rate:.1f}%)")
    if false_positives:
        print(f"  FP projects: {false_positives}")
    else:
        print(f"  All {len(PROJECTS)} projects passed (zero false positives)")

    # By category
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "fp": 0}
        categories[cat]["total"] += 1
        if r["is_false_positive"]:
            categories[cat]["fp"] += 1

    print(f"\n  By category:")
    for cat, stats in sorted(categories.items()):
        print(f"    {cat:12s}: {stats['fp']}/{stats['total']} FP")

    # Save
    csv_path = OUTPUT_DIR / "real_world_50_projects.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Project", "Stars", "Category", "Behaviors", "Decision", "Privilege", "FP"])
        for r in results:
            writer.writerow([r["name"], r["stars"], r["category"],
                             r["behaviors_count"], r["decision"],
                             r["derived_privilege"], r["is_false_positive"]])
    print(f"\nSaved to {csv_path}")


if __name__ == "__main__":
    main()
