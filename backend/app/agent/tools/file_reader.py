"""
文件读取工具

让 LLM 能够查看用户上传的数据文件内容。
支持 CSV / Excel / JSON 三种格式。
"""

import json
import pandas as pd
from pathlib import Path

from .base import BaseTool


class FileReaderTool(BaseTool):
    """读取数据文件的内容，以文本形式返回给 LLM"""

    # ── 抽象属性实现 ─────────────────────────────────

    @property
    def name(self) -> str:
        return "read_file"

    @property
    def description(self) -> str:
        return (
            "读取用户上传的数据文件内容。"
            "支持 CSV (.csv)、Excel (.xlsx/.xls)、JSON (.json) 格式。"
            "返回文件前若干行文本，适合查看数据原始内容。"
        )

    # ── 核心逻辑 ─────────────────────────────────────

    MAX_ROWS = 50   # 最多返回 50 行，避免内容撑爆 LLM 上下文

    def run(self, file_path: str = "", max_rows: int = MAX_ROWS) -> str:
        """读取文件并返回文本内容"""
        path = Path(file_path)
        rows = min(max_rows, self.MAX_ROWS)

        if not path.exists():
            return f"[错误] 文件不存在: {file_path}"

        ext = path.suffix.lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(path, nrows=rows)
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(path, nrows=rows)
            elif ext == ".json":
                return self._read_json(path, rows)
            else:
                return f"[错误] 不支持的文件格式: {ext}，仅支持 CSV/Excel/JSON"

            lines = [f"文件: {path.name}  |  共显示 {len(df)} 行 × {len(df.columns)} 列", ""]
            lines.append(df.to_string(index=False))
            return "\n".join(lines)

        except Exception as e:
            return f"[错误] 读取文件失败: {str(e)}"

    def _read_json(self, path: Path, rows: int) -> str:
        """单独处理 JSON，因为它可能需要格式化"""
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # 如果是 list of dict → 转成 DataFrame 展示
            if isinstance(data, list) and all(isinstance(item, dict) for item in data[:1]):
                df = pd.DataFrame(data).head(rows)
                return f"文件: {path.name}  |  JSON 数组，共 {len(data)} 条记录\n\n" + df.to_string(index=False)
            # 其他 JSON → 格式化字符串
            return json.dumps(data, ensure_ascii=False, indent=2)[:3000]

    # ── Schema ───────────────────────────────────────

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要读取的文件绝对路径，从用户上传文件列表中获取"
                }
            },
            "required": ["file_path"]
        }
