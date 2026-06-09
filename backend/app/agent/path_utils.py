"""上传文件路径在宿主机与 Docker 沙箱之间的转换。"""

import os
import re

SANDBOX_UPLOADS_ROOT = os.getenv("SANDBOX_UPLOADS_ROOT", "/data/uploads")


def to_sandbox_path(storage_path: str, sandbox_root: str = SANDBOX_UPLOADS_ROOT) -> str:
    """将宿主机上的 uploads 绝对路径转为沙箱内可读路径。"""
    normalized = storage_path.replace("\\", "/")
    marker = "/uploads/"
    idx = normalized.lower().find(marker)
    if idx != -1:
        rel = normalized[idx + len(marker):]
        return f"{sandbox_root.rstrip('/')}/{rel}"
    return storage_path


def prepare_code_for_sandbox(code: str, files) -> str:
    """把代码中的宿主机文件路径替换为沙箱路径。"""
    if not code or not files:
        return code

    replacements: list[tuple[str, str]] = []
    for f in files:
        host_path = f.storage_path
        sandbox_path = to_sandbox_path(host_path)
        if host_path == sandbox_path:
            continue
        replacements.append((host_path, sandbox_path))
        replacements.append((host_path.replace("\\", "/"), sandbox_path))
        replacements.append((host_path.replace("\\", "\\\\"), sandbox_path))

    # 长路径优先，避免短路径误替换
    for old, new in sorted(replacements, key=lambda x: len(x[0]), reverse=True):
        code = code.replace(old, new)

    # 兜底：匹配 uploads/{session_id}/{filename}
    def _rewrite_uploads_match(match: re.Match) -> str:
        return f"{SANDBOX_UPLOADS_ROOT.rstrip('/')}/{match.group(1)}/{match.group(2)}"

    code = re.sub(
        r"(?:[A-Za-z]:)?[/\\]+[^\"'\n]*?[/\\]uploads[/\\](\d+)[/\\]([^\"'\s\\]+)",
        _rewrite_uploads_match,
        code,
    )
    return code
