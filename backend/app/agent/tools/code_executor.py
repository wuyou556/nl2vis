"""
代码执行工具

将 LLM 生成的 Python 代码发送到 Docker 沙箱执行，返回 stdout/stderr。

这是整个 Agent 最核心的工具——数据分析、图表生成、统计计算都靠它。
"""

import httpx
import logging

from .base import BaseTool

logger = logging.getLogger(__name__)


class CodeExecutorTool(BaseTool):
    """在 Docker 沙箱中执行 Python 代码"""

    def __init__(self, sandbox_url: str = "http://localhost:5001", timeout: int = 30):
        self._sandbox_url = sandbox_url.rstrip("/")
        self._timeout = timeout

    # ── 抽象属性 ────────────────────────────────────

    @property
    def name(self) -> str:
        return "execute_code"

    @property
    def description(self) -> str:
        return (
            "在安全的 Docker 沙箱环境中执行 Python 代码。"
            "可以用于：数据分析（pandas）、统计计算（numpy）、"
            "生成图表数据（JSON）、数据清洗和转换。"
            "沙箱限制：超时最多 30 秒，输出最多 64KB，无网络访问。"
            "用户上传的文件挂载在 /data/uploads/<session_id>/<filename>，"
            "读取数据时请使用该 Linux 路径，不要使用 Windows 盘符路径。"
            "代码中请用 print() 输出关键结果，这些会作为返回值传回来。"
            "如果代码执行出错，查看 stderr 中的错误信息，修复后重试。"
        )

    # ── 核心逻辑 ────────────────────────────────────

    def run(self, code: str = "", timeout: int = None) -> str:
        """
        发送代码到沙箱执行。

        Args:
            code: Python 代码字符串
            timeout: 超时秒数，不传则用默认值
        """
        if not code.strip():
            return "[错误] 代码为空，请提供要执行的 Python 代码"

        timeout = timeout or self._timeout

        try:
            response = httpx.post(
                f"{self._sandbox_url}/execute",
                json={"code": code, "timeout": timeout},
                timeout=httpx.Timeout(timeout + 5),  # 比沙箱超时多 5 秒，给网络留余量
            )
            response.raise_for_status()
            data = response.json()

            return self._format_result(data)

        except httpx.ConnectError:
            return (
                f"[错误] 无法连接到沙箱 ({self._sandbox_url})。"
                "请确认 Docker 沙箱已启动：docker-compose up -d sandbox"
            )
        except httpx.TimeoutException:
            return f"[错误] 沙箱执行超时（{timeout}s），请优化代码或增加超时时间"
        except Exception as e:
            logger.error(f"沙箱调用异常: {e}")
            return f"[错误] 沙箱调用失败: {str(e)}"

    def _format_result(self, data: dict) -> str:
        """
        把沙箱的 JSON 响应整理成 LLM 易读的文本。

        沙箱返回格式：
            {stdout, stderr, exit_code, truncated}
        """
        parts = []

        if data.get("stdout"):
            parts.append("[stdout]\n" + data["stdout"].rstrip())

        if data.get("stderr"):
            parts.append("[stderr]\n" + data["stderr"].rstrip())

        if data.get("truncated"):
            parts.append("[注意] 输出已被截断，请精简输出内容")

        if data.get("exit_code", 0) != 0:
            parts.insert(0, f"[执行失败] exit_code={data['exit_code']}")

        if not parts:
            parts.append("[提示] 代码执行完成，无输出。请用 print() 输出关键结果。")

        return "\n\n".join(parts)

    # ── Schema ───────────────────────────────────────

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "code": {
                    "type": "string",
                    "description": "要执行的 Python 代码。用 print() 输出关键结果。"
                }
            },
            "required": ["code"]
        }
