"""
沙箱 Python 执行器 API。
提供健康检查与受超时限制的代码执行接口。
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

DEFAULT_TIMEOUT = int(os.getenv("EXECUTOR_TIMEOUT", "30"))
MAX_OUTPUT = int(os.getenv("EXECUTOR_MAX_OUTPUT", "65536"))
WORK_DIR = Path(os.getenv("SANDBOX_WORK_DIR", "/tmp/sandbox-work"))


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "sandbox-executor"})


@app.post("/execute")
def execute():
    payload = request.get_json(silent=True) or {}
    code = payload.get("code")
    if not code or not isinstance(code, str):
        return jsonify({"error": "Missing or invalid 'code' field"}), 400

    timeout = payload.get("timeout", DEFAULT_TIMEOUT)
    try:
        timeout = max(1, min(int(timeout), 120))
    except (TypeError, ValueError):
        timeout = DEFAULT_TIMEOUT

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    script_name = f"run_{uuid.uuid4().hex}.py"
    script_path = WORK_DIR / script_name

    try:
        script_path.write_text(code, encoding="utf-8")
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(WORK_DIR),
            env={
                "PATH": os.environ.get("PATH", ""),
                "HOME": os.environ.get("HOME", "/home/sandbox"),
                "PYTHONUNBUFFERED": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )
        stdout = _truncate(result.stdout)
        stderr = _truncate(result.stderr)
        return jsonify(
            {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": result.returncode,
                "truncated": len(result.stdout) > MAX_OUTPUT or len(result.stderr) > MAX_OUTPUT,
            }
        )
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Execution timed out", "timeout": timeout}), 408
    except OSError as exc:
        return jsonify({"error": str(exc)}), 500
    finally:
        script_path.unlink(missing_ok=True)


def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT:
        return text
    return text[:MAX_OUTPUT] + "\n... [output truncated]"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
