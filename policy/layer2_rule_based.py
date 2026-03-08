"""
Non-LLM Layer2 Baseline: Rule-Based Behavior Extraction

This implementation demonstrates that Layer2 can be implemented WITHOUT LLM,
using only deterministic pattern matching and AST parsing.

Purpose: Prove that CodeGuard's core value is the architecture (schema + policy),
not the LLM implementation.
"""

import re
import ast
import base64
from typing import List, Dict, Any


class RuleBasedLayer2:
    """
    Rule-based behavior extractor that outputs the same Frozen Schema as LLM-based Layer2.

    Coverage: Focuses on the most common patterns in SemiReal-60 v2 benchmark.
    """

    def __init__(self):
        self.safe_hosts = {'pypi.org', 'files.pythonhosted.org', 'github.com', 'huggingface.co'}

    def extract_behaviors(self, files_content: str) -> List[Dict[str, Any]]:
        """
        Extract behaviors from repository files using rule-based pattern matching.

        Returns: List of behaviors conforming to Frozen Schema
        """
        behaviors = []

        # Parse files
        files = self._parse_files(files_content)

        for filename, content in files.items():
            if filename.endswith('.py'):
                behaviors.extend(self._extract_from_python(content))
            elif filename.endswith('.yml') or filename.endswith('.yaml'):
                behaviors.extend(self._extract_from_ci(content))
            elif filename == 'Makefile':
                behaviors.extend(self._extract_from_makefile(content))

        return behaviors

    def _parse_files(self, files_content: str) -> Dict[str, str]:
        """Parse files section from repo snapshot."""
        files = {}
        current_file = None
        current_content = []

        for line in files_content.split('\n'):
            if line.strip().startswith('- ') and ':' in line:
                # Save previous file
                if current_file:
                    files[current_file] = '\n'.join(current_content)
                # Start new file
                current_file = line.split(':')[0].strip('- ').strip()
                current_content = []
            elif current_file:
                # Remove leading spaces (YAML indentation)
                current_content.append(line[4:] if line.startswith('    ') else line)

        # Save last file
        if current_file:
            files[current_file] = '\n'.join(current_content)

        return files

    def _extract_from_python(self, content: str) -> List[Dict[str, Any]]:
        """Extract behaviors from Python source code using AST."""
        behaviors = []

        try:
            tree = ast.parse(content)
        except:
            # Fallback to regex if AST parsing fails
            return self._extract_from_python_regex(content)

        for node in ast.walk(tree):
            # Network operations
            if isinstance(node, ast.Call):
                if self._is_requests_call(node):
                    behaviors.append(self._handle_requests(node, content))
                elif self._is_subprocess_call(node):
                    behaviors.append(self._handle_subprocess(node, content))

            # File operations
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id == 'open':
                    behaviors.append(self._handle_file_op(node, content))

            # ENV_ACCESS
            if isinstance(node, ast.Subscript):
                if self._is_env_access(node):
                    behaviors.append(self._handle_env_access(node))

        return [b for b in behaviors if b]  # Filter None

    def _extract_from_python_regex(self, content: str) -> List[Dict[str, Any]]:
        """Fallback regex-based extraction for Python."""
        behaviors = []

        # requests.post/get
        if re.search(r'requests\.(post|get)', content):
            method = re.search(r'requests\.(post|get)', content).group(1)
            data_flow = 'UPLOAD_EXFIL' if method == 'post' and 'data=' in content else 'DOWNLOAD_ONLY'
            behaviors.append({
                'action': 'NETWORK_CONNECT',
                'target_type': 'EXTERNAL_DOMAIN',
                'target_pattern': 'LITERAL_STRING',
                'obfuscation_scope': 'NONE',
                'data_flow': data_flow,
                'target_value': None
            })

        # subprocess/os.system
        if re.search(r'subprocess\.(run|call|Popen)|os\.system', content):
            # Check for obfuscation
            obfusc = 'NONE'
            pattern = 'LITERAL_STRING'
            if 'base64.b64decode' in content:
                obfusc = 'PAYLOAD_HIDING'
                pattern = 'BASE64'
            elif re.search(r'_\w+\s*\+\s*_\w+', content):  # String concatenation
                obfusc = 'TARGET_HIDING'
                pattern = 'CONCATENATION'

            behaviors.append({
                'action': 'EXEC_CMD',
                'target_type': 'UNKNOWN',
                'target_pattern': pattern,
                'obfuscation_scope': obfusc,
                'data_flow': 'NONE',
                'target_value': None
            })

        return behaviors

    def _extract_from_ci(self, content: str) -> List[Dict[str, Any]]:
        """Extract behaviors from CI configuration files."""
        behaviors = []

        # Look for run: steps
        for line in content.split('\n'):
            if re.match(r'\s*-?\s*run:', line):
                cmd = line.split('run:')[1].strip()

                # pip install / poetry install / pipx install
                if re.search(r'(pip|poetry|pipx)\s+install', cmd):
                    behaviors.append({
                        'action': 'NETWORK_CONNECT',
                        'target_type': 'PACKAGE_REPO',
                        'target_pattern': 'LITERAL_STRING',
                        'obfuscation_scope': 'NONE',
                        'data_flow': 'DOWNLOAD_ONLY',
                        'target_value': 'pypi.org'
                    })

                # Dangerous commands (MOCK_*)
                elif re.search(r'MOCK_(DANGEROUS|SYSTEM)', cmd):
                    behaviors.append({
                        'action': 'EXEC_CMD',
                        'target_type': 'UNKNOWN',
                        'target_pattern': 'LITERAL_STRING',
                        'obfuscation_scope': 'NONE',
                        'data_flow': 'NONE',
                        'target_value': None
                    })

        return behaviors

    def _extract_from_makefile(self, content: str) -> List[Dict[str, Any]]:
        """Extract behaviors from Makefile."""
        behaviors = []

        # Look for dangerous patterns in Makefile
        for line in content.split('\n'):
            # String concatenation in commands
            if re.search(r'\$\(\w+\)\$\(\w+\)', line) or re.search(r'\$\{[^}]+\}\$\{[^}]+\}', line):
                behaviors.append({
                    'action': 'EXEC_CMD',
                    'target_type': 'UNKNOWN',
                    'target_pattern': 'CONCATENATION',
                    'obfuscation_scope': 'TARGET_HIDING',
                    'data_flow': 'NONE',
                    'target_value': None
                })

        return behaviors

    def _is_requests_call(self, node: ast.Call) -> bool:
        """Check if node is requests.post/get call."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id == 'requests' and node.func.attr in ['post', 'get']
        return False

    def _is_subprocess_call(self, node: ast.Call) -> bool:
        """Check if node is subprocess call."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                return node.func.value.id in ['subprocess', 'os']
        return False

    def _is_env_access(self, node: ast.Subscript) -> bool:
        """Check if node is os.environ[key] read."""
        if isinstance(node.value, ast.Attribute):
            if isinstance(node.value.value, ast.Name):
                return node.value.value.id == 'os' and node.value.attr == 'environ'
        return False

    def _handle_requests(self, node: ast.Call, content: str) -> Dict[str, Any]:
        """Handle requests.post/get calls."""
        method = node.func.attr

        # Determine data_flow
        data_flow = 'DOWNLOAD_ONLY'
        if method == 'post':
            # Check if uploading local data
            for keyword in node.keywords:
                if keyword.arg == 'data':
                    data_flow = 'UPLOAD_EXFIL'
                    break

        return {
            'action': 'NETWORK_CONNECT',
            'target_type': 'EXTERNAL_DOMAIN',
            'target_pattern': 'LITERAL_STRING',
            'obfuscation_scope': 'NONE',
            'data_flow': data_flow,
            'target_value': None
        }

    def _handle_subprocess(self, node: ast.Call, content: str) -> Dict[str, Any]:
        """Handle subprocess/os.system calls."""
        # Check for obfuscation
        obfusc = 'NONE'
        pattern = 'LITERAL_STRING'

        # Check for base64 decoding
        if 'base64.b64decode' in content:
            obfusc = 'PAYLOAD_HIDING'
            pattern = 'BASE64'
        # Check for string concatenation
        elif any(isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add) for arg in node.args):
            obfusc = 'TARGET_HIDING'
            pattern = 'CONCATENATION'

        return {
            'action': 'EXEC_CMD',
            'target_type': 'UNKNOWN',
            'target_pattern': pattern,
            'obfuscation_scope': obfusc,
            'data_flow': 'NONE',
            'target_value': None
        }

    def _handle_file_op(self, node: ast.Call, content: str) -> Dict[str, Any]:
        """Handle file operations."""
        # Determine if read or write
        mode = 'r'
        for keyword in node.keywords:
            if keyword.arg == 'mode':
                if isinstance(keyword.value, ast.Constant):
                    mode = keyword.value.value

        action = 'FILE_WRITE' if 'w' in mode or 'a' in mode else 'FILE_READ'

        return {
            'action': action,
            'target_type': 'LOCAL_PATH',
            'target_pattern': 'LITERAL_STRING',
            'obfuscation_scope': 'NONE',
            'data_flow': 'LOCAL_OP',
            'target_value': None
        }

    def _handle_env_access(self, node: ast.Subscript) -> Dict[str, Any]:
        """Handle os.environ[key] access."""
        # Only extract if it's a read (in Load context)
        if isinstance(node.ctx, ast.Load):
            return {
                'action': 'ENV_ACCESS',
                'target_type': 'SYSTEM_ENV',
                'target_pattern': 'LITERAL_STRING',
                'obfuscation_scope': 'NONE',
                'data_flow': 'NONE',
                'target_value': None
            }
        return None


def extract_files_section(repo_snapshot: str) -> str:
    """Extract files section from repo snapshot."""
    if not repo_snapshot:
        return ""
    lines = repo_snapshot.strip().split("\n")
    result = []
    in_files = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("files:"):
            in_files = True
            continue
        if stripped.startswith("README:") or stripped.startswith("notes:"):
            in_files = False
            continue
        if in_files:
            result.append(line)
    return "\n".join(result).strip() if result else ""
