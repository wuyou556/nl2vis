"""
工具抽象基类

所有工具（代码执行、文件读取、数据预览）都继承 BaseTool，
必须实现 name、description、run 三个成员。
"""

from abc import ABC, abstractmethod


class BaseTool(ABC):
    """所有工具的抽象基类 —— 定义了统一的调用接口"""

    # ── 抽象属性：子类必须 override ──────────────

    @property
    @abstractmethod
    def name(self) -> str:
        """
        工具名称，如 'execute_code'、'data_preview'。

        LLM 通过名称来选择和调用工具。
        """
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """
        工具的功能描述。

        这段文字会被嵌入系统提示词，告诉 LLM 这个工具能做什么、
        什么时候应该用它。
        """
        ...

    # ── 抽象方法：子类必须 override ──────────────

    @abstractmethod
    def run(self, **kwargs) -> str:
        """
        执行工具，返回结果字符串。

        Args:
            **kwargs: 工具参数，由 LLM 的 Action Input 反序列化后传入

        Returns:
            工具执行的结果文本（成功时返回内容，失败时返回错误信息）
        """
        ...

    # ── 默认方法：子类按需 override ───────────────

    def get_schema(self) -> dict:
        """
        返回工具参数的 JSON Schema。

        告诉 LLM 这个工具接受哪些参数，有助于 LLM 正确生成参数。

        示例:
            {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "要执行的 Python 代码"}
                },
                "required": ["code"]
            }
        """
        return {}
