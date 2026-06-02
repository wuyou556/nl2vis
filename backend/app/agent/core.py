"""
AgentExecutor — ReAct 主循环

负责：
1. 组装上下文（系统提示词 + 历史 + 用户消息）
2. 驱动 Think → Act → Observe 循环
3. 解析 LLM 输出，调用工具，最终返回结果
"""

import json
import logging
import re

from .schemas import AgentAction, AgentObservation, AgentStep, AgentResult
from .prompts import get_system_prompt
from .tools import build_tools_description

logger = logging.getLogger(__name__)


class AgentExecutor:
    """ReAct Agent 核心引擎"""

    def __init__(self, llm_client, tools, memory, settings):
        self.llm = llm_client
        self.tools = {t.name: t for t in tools}
        self.memory = memory
        self.settings = settings
        self.max_iterations = settings.max_iterations

    def run(self, user_message: str, session_id: int, files, history) -> AgentResult:
        """主入口：接收用户消息，执行 ReAct 循环，返回结果。"""
        # ── 准备阶段 ──────────────────────────────
        system_prompt = get_system_prompt(build_tools_description())
        file_info = self._format_file_info(files)
        message_history = self.memory.load_history(history)

        messages = self.memory.build_messages(
            system_prompt=system_prompt,
            history=message_history,
            user_message=user_message + file_info,
            agent_steps=[],
        )

        steps = []

        # ── ReAct 循环 ────────────────────────────
        for i in range(self.max_iterations):
            # ① 调用 LLM
            response = self.llm.chat.completions.create(
                model=self.settings.model_name,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )
            llm_text = response.choices[0].message.content

            if self.settings.verbose:
                logger.info(f"[Iteration {i+1}] LLM output:\n{llm_text[:500]}...")

            # ② 解析输出
            action = self._parse_llm_output(llm_text)

            if action is None:
                # Final Answer → 结束
                return AgentResult(
                    output=llm_text.split("Final Answer:")[-1].strip(),
                    steps=steps,
                    iterations=i + 1,
                )

            # ③ 调用工具
            observation = self._call_tool(action.tool, action.tool_input)
            step = AgentStep(action=action, observation=observation)
            steps.append(step)

            if self.settings.verbose:
                logger.info(f"[Step {i+1}] {action.tool} → success={observation.success}")

            # ④ 把结果追加回消息（下一轮 LLM 才知道发生了什么）
            messages.append({"role": "assistant", "content": llm_text})
            messages.append({
                "role": "system",
                "content": f"工具 '{action.tool}' 执行结果:\n{observation.result}"
            })

        # 超过最大迭代次数 → 强制结束
        return AgentResult(
            output="分析步数超出限制，请简化你的问题后重试。",
            steps=steps,
            iterations=self.max_iterations,
        )




    def _format_file_info(self, files) -> str:
        """把 File 对象列表转成一段可用文件提示"""
        if not files:
            return ""

        lines = ["", "📁 可用文件（请使用以下路径读取）："]
        for f in files:
            lines.append(f"  - {f.filename} → {f.storage_path}")
        return "\n".join(lines)

    def _parse_llm_output(self, text: str) -> AgentAction | None:
        """解析 LLM 输出。有 Action → AgentAction，有 Final Answer → None"""
        if "Final Answer:" in text:
            return None

        if "Action:" not in text:
            raise ValueError(f"LLM 输出既没有 Action 也没有 Final Answer:\n{text[:300]}")

        # Thought
        thought = ""
        thought_match = re.search(r"Thought:\s*(.*?)(?=Action:|\Z)", text, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # 工具名
        action_match = re.search(r"Action:\s*(\S+)", text)
        tool_name = action_match.group(1).strip() if action_match else ""

        # 工具参数（JSON）
        tool_input = {}
        input_match = re.search(r"Action Input:\s*(\{.*?\})", text, re.DOTALL)
        if input_match:
            try:
                tool_input = json.loads(input_match.group(1))
            except json.JSONDecodeError as e:
                raise ValueError(f"Action Input JSON 解析失败: {e}")

        return AgentAction(
            tool=tool_name,
            tool_input=tool_input,
            thought=thought,
            log=text,
        )

    def _call_tool(self, tool_name: str, tool_input: dict) -> AgentObservation:
        """按名查找工具并执行，失败时返回包含错误信息的 Observation"""
        tool = self.tools.get(tool_name)
        if tool is None:
            return AgentObservation(
                tool=tool_name,
                result=f"[错误] 未知的工具 '{tool_name}'。可用: {list(self.tools.keys())}",
                success=False,
            )

        try:
            result = tool.run(**tool_input)
            success = "[错误]" not in result
            return AgentObservation(tool=tool_name, result=result, success=success)
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行异常: {e}")
            return AgentObservation(
                tool=tool_name,
                result=f"[错误] 工具执行异常: {str(e)}",
                success=False,
            )
