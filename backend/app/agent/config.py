"""
Agent 配置管理

负责：
1. 从环境变量读取 LLM 和 Agent 的配置
2. 初始化 OpenAI 兼容的 LLM 客户端（支持 DeepSeek / 通义千问 / 智谱 等）
"""

import os
from dataclasses import dataclass
from openai import OpenAI


# ══════════════════════════════════════════════════════════════════
#  Settings dataclass —— 集中存放所有 Agent 配置
# ══════════════════════════════════════════════════════════════════

@dataclass
class AgentSettings:
    """所有字段都有默认值，即使 .env 没配也不会崩溃"""

    # LLM 相关
    model_name: str = "deepseek-chat"
    api_key: str = "sk-your-api-key-here"
    base_url: str = "https://api.deepseek.com/v1"
    temperature: float = 0.0
    max_tokens: int = 4096

    # Agent 行为
    max_iterations: int = 10
    tool_timeout: int = 30
    verbose: bool = True

    # 外部服务
    sandbox_url: str = "http://localhost:5001"


# ══════════════════════════════════════════════════════════════════
#  工厂函数 —— 从环境变量拼出一个配置实例
# ══════════════════════════════════════════════════════════════════

def get_agent_config() -> AgentSettings:
    """从 .env 读取配置，读不到就用 dataclass 默认值"""

    return AgentSettings(
        model_name=os.getenv("LLM_MODEL_NAME", "deepseek-chat"),
        api_key=os.getenv("LLM_API_KEY", "sk-your-api-key-here"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.0")),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
        max_iterations=int(os.getenv("AGENT_MAX_ITERATIONS", "10")),
        tool_timeout=int(os.getenv("AGENT_TOOL_TIMEOUT", "30")),
        verbose=os.getenv("AGENT_VERBOSE", "true").lower() == "true",
        sandbox_url=os.getenv("SANDBOX_URL", "http://localhost:5001"),
    )


# ══════════════════════════════════════════════════════════════════
#  LLM 客户端初始化
# ══════════════════════════════════════════════════════════════════

def create_llm_client(settings: AgentSettings | None = None) -> OpenAI:
    """
    返回一个 OpenAI 兼容客户端。

    不传 settings 就自动从环境变量读。
    用法：
        client = create_llm_client()
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "你好"}],
        )
    """

    if settings is None:
        settings = get_agent_config()

    return OpenAI(
        api_key=settings.api_key,
        base_url=settings.base_url,
    )
