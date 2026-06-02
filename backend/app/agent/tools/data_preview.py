"""
数据预览工具

比 file_reader 更进一步——不只看原始内容，而是分析数据结构：
列名、类型、空值情况、基本统计等。

这个工具通常是 Agent 的第一步：先预览数据，搞清楚结构，再决定怎么做。
"""

import pandas as pd
from pathlib import Path

from .base import BaseTool


class DataPreviewTool(BaseTool):
    """快速预览数据文件的整体结构"""

    @property
    def name(self) -> str:
        return "data_preview"

    @property
    def description(self) -> str:
        return (
            "快速预览数据文件的结构信息。"
            "返回内容包括：行列数、列名及数据类型、前5行数据、基本统计摘要。"
            "在编写数据分析代码之前，应该先调用此工具了解数据结构。"
            "支持 CSV / Excel 格式。"
        )

    # ── 核心逻辑 ─────────────────────────────────────

    def run(self, file_path: str = "") -> str:
        """读取文件并返回结构化的预览信息"""
        path = Path(file_path)

        if not path.exists():
            return f"[错误] 文件不存在: {file_path}"

        ext = path.suffix.lower()
        try:
            if ext == ".csv":
                df = pd.read_csv(path)
            elif ext in (".xlsx", ".xls"):
                df = pd.read_excel(path)
            else:
                return f"[错误] data_preview 不支持 {ext} 格式，仅支持 CSV/Excel"

            if df.empty:
                return f"[警告] 文件 {path.name} 为空（0 行）"

            return self._format_preview(path.name, df)

        except Exception as e:
            return f"[错误] 预览文件失败: {str(e)}"

    def _format_preview(self, filename: str, df: pd.DataFrame) -> str:
        """
        组织预览信息的输出格式。

        分四个区块：
        1. 基本信息（行列数）
        2. 列信息（名称 + 类型）
        3. 前 5 行
        4. 数值列统计（describe）
        """
        lines = [f"📁 {filename}  ——  共 {df.shape[0]} 行 × {df.shape[1]} 列", ""]

        # 1. 列信息
        lines.append("── 列名和类型 ──")
        for col in df.columns:
            lines.append(f"  {col}: {df[col].dtype}")
        lines.append("")

        # 2. 前 5 行
        lines.append("── 前 5 行 ──")
        lines.append(df.head(5).to_string(index=False))
        lines.append("")

        # 3. 数值列统计（有数值列才显示）
        numeric_cols = df.select_dtypes(include=["number"]).columns
        if len(numeric_cols) > 0:
            lines.append("── 数值列统计 ──")
            lines.append(df[numeric_cols].describe().to_string())
            lines.append("")

        # 4. 缺失值提示
        missing = df.isnull().sum()
        if missing.any():
            lines.append("── 缺失值 ──")
            for col in df.columns:
                if missing[col] > 0:
                    lines.append(f"  {col}: {missing[col]} 个缺失值")

        return "\n".join(lines)

    # ── Schema ───────────────────────────────────────

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "要预览的文件绝对路径"
                }
            },
            "required": ["file_path"]
        }
