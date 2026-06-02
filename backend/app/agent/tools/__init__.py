"""
工具注册表

集中管理所有 Tool 实例，提供统一的查询和调用入口。

使用方式:
    from app.agent.tools import get_tool, get_tools, build_tools_description

    tool = get_tool("execute_code")          # 按名取工具
    result = tool.run(code="print(1+1)")     # 调用工具

    all_tools = get_tools()                  # 获取所有工具
    desc = build_tools_description()         # 生成工具描述文本（嵌入 prompt）
"""

from .base import BaseTool
from .file_reader import FileReaderTool
from .data_preview import DataPreviewTool
from .code_executor import CodeExecutorTool


# ── 工具注册表 ──────────────────────────────────────────────

def _build_registry() -> dict[str, BaseTool]:
    """
    构建工具注册表。

    如果要新增工具，在这里 new 一个实例加进去即可。
    CodeExecutorTool 需要传 sandbox_url，后续在 AgentExecutor 初始化时
    会从 AgentSettings 传入真实地址。
    """
    return {
        "read_file":    FileReaderTool(),
        "data_preview": DataPreviewTool(),
        "execute_code": CodeExecutorTool(),
    }


TOOL_REGISTRY: dict[str, BaseTool] = _build_registry()


# ── 对外 API ────────────────────────────────────────────────

def get_tools() -> list[BaseTool]:
    """返回所有工具实例的列表"""
    return list(TOOL_REGISTRY.values())


def get_tool(name: str) -> BaseTool | None:
    """
    按名称获取工具，找不到返回 None。

    这样 AgentExecutor._parse_llm_output 解析出工具名后可以直接取。
    """
    return TOOL_REGISTRY.get(name)


def build_tools_description() -> str:
    """
    生成所有工具的描述文本，用于嵌入系统提示词。

    LLM 通过这段文本来了解自己有哪些工具可用、每种工具怎么用。

    输出格式示例:
        - execute_code: 在 Docker 沙箱中执行 Python 代码
        参数: code (string, 必填) — 要执行的代码
        - data_preview: 预览数据文件结构
        参数: file_path (string, 必填) — 文件路径
    """
    lines = []
    for tool in TOOL_REGISTRY.values():
        schema = tool.get_schema()
        params = ""
        if schema and "properties" in schema:
            required = schema.get("required", [])
            param_parts = []
            for pname, pinfo in schema["properties"].items():
                req_mark = "必填" if pname in required else "可选"
                param_parts.append(f"{pname} ({pinfo.get('type', 'any')}, {req_mark}) — {pinfo.get('description', '')}")
            params = "  参数: " + " ; ".join(param_parts)

        lines.append(f"- **{tool.name}**: {tool.description}")
        if params:
            lines.append(params)

    return "\n".join(lines)


def update_sandbox_url(url: str) -> None:
    """
    更新 CodeExecutorTool 的沙箱地址。

    在 AgentExecutor 初始化时调用，把 AgentSettings.sandbox_url 注入工具。
    """
    executor = TOOL_REGISTRY.get("execute_code")
    if isinstance(executor, CodeExecutorTool):
        executor._sandbox_url = url.rstrip("/")
