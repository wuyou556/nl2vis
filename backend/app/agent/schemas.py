"""
Agent 核心数据结构

这四个 dataclass 构成 Agent 运行过程中的"语言"——
其他模块（core、tools、memory）都依赖它们来交换数据。
"""

from dataclasses import dataclass, field


# ──────────────────────────────────────────────────────────────────
#  1. AgentAction — LLM 决定调用工具时产生
# ──────────────────────────────────────────────────────────────────

@dataclass
class AgentAction:
    """LLM 解析出的一个工具调用指令"""

    tool: str
    """要调用的工具名称，比如 'execute_code'、'data_preview'"""

    tool_input: dict
    """传给工具的参数，比如 {'code': 'print(1+1)'} 或 {'file_path': 'uploads/1/data.csv'}"""

    thought: str = ""
    """LLM 输出的思考过程（Thought: ... 部分），用于前端展示和调试"""

    log: str = ""
    """LLM 原始输出全文，调试用，前端可不展示"""


# ──────────────────────────────────────────────────────────────────
#  2. AgentObservation — 工具执行完后返回的结果
# ──────────────────────────────────────────────────────────────────

@dataclass
class AgentObservation:
    """工具调用后的观察结果"""

    tool: str
    """调用了哪个工具"""

    result: str
    """工具返回的文本内容（stdout 或错误信息）"""

    success: bool = True
    """执行是否成功。False 时 result 里是错误信息，LLM 会据此重试或修复"""


# ──────────────────────────────────────────────────────────────────
#  3. AgentStep — 一个完整的 Think→Act→Observe 单元
# ──────────────────────────────────────────────────────────────────

@dataclass
class AgentStep:
    """ReAct 循环中的一步 = 一次动作 + 一次观察"""

    action: AgentAction
    """LLM 决定做什么"""

    observation: AgentObservation
    """做完之后发生了什么"""


# ──────────────────────────────────────────────────────────────────
#  4. AgentResult — Agent 最终返回给路由层的产物
# ──────────────────────────────────────────────────────────────────

@dataclass
class AgentResult:
    """Agent 完成一次对话的最终结果"""

    output: str
    """给用户看的最终回复文本（LLM 的 Final Answer）"""

    steps: list[AgentStep] = field(default_factory=list)
    """所有中间步骤记录，前端可以据此展示 Agent 的思考过程"""

    iterations: int = 0
    """实际循环次数"""

    token_usage: dict = field(default_factory=dict)
    """Token 消耗统计，形如 {'prompt_tokens': 1200, 'completion_tokens': 300}"""
