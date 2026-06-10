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
from .path_utils import to_sandbox_path, prepare_code_for_sandbox

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

        filenames = [f.filename for f in files] if files else []
        messages = self.memory.build_messages(
            system_prompt=system_prompt,
            history=message_history,
            user_message=user_message + file_info,
            agent_steps=[],
            filenames = filenames
        )

        steps = []
        self._session_files = files

        # ── ReAct 循环 ────────────────────────────
        for i in range(self.max_iterations):
            # ① 调用 LLM
            response = self.llm.chat.completions.create(
                model=self.settings.model_name,
                messages=messages,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens,
            )
            choice = response.choices[0]
            llm_text = self._normalize_llm_text(choice.message.content)
            finish_reason = getattr(choice, "finish_reason", None)

            if self.settings.verbose:
                preview = llm_text[:500] if llm_text else "(empty)"
                logger.info(
                    f"[Iteration {i+1}] LLM output (finish_reason={finish_reason}):\n{preview}"
                    + ("..." if len(llm_text) > 500 else "")
                )

            # ② 解析输出
            action = self._parse_llm_output(llm_text)
            if action is False:
                messages.append({"role": "assistant", "content": llm_text or "(empty)"})
                messages.append({
                    "role": "system",
                    "content": (
                        "你的上一次回复为空或格式不正确。"
                        "请严格使用 Thought + Action + Action Input，"
                        "或 Thought + Final Answer 格式重新输出。"
                    ),
                })
                continue

            if action is None:
                # Final Answer → 结束
                return AgentResult(
                    output=self._extract_final_answer(llm_text),
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

        lines = ["", "📁 可用文件："]
        for f in files:
            sandbox_path = to_sandbox_path(f.storage_path)
            lines.append(f"  - {f.filename}")
            lines.append(f"    data_preview / read_file: {f.storage_path}")
            lines.append(f"    execute_code（沙箱内）: {sandbox_path}")
        return "\n".join(lines)

    def _normalize_llm_text(self, text: str | None) -> str:
        """清理 LLM 原始输出，去掉 markdown 代码块包裹。"""
        if not text:
            return ""
        text = text.strip()
        fence_match = re.match(r"^```(?:\w+)?\s*\n?(.*?)\n?```\s*$", text, re.DOTALL)
        if fence_match:
            text = fence_match.group(1).strip()
        return text

    def _parse_llm_output(self, text: str) -> AgentAction | None | bool:
        """
        解析 LLM 输出。
        - AgentAction: 需要调用工具
        - None: Final Answer，结束循环
        - False: 无法解析，请求 LLM 重试
        """
        if not text.strip():
            return False

        if re.search(r"(?:Final Answer|最终答案)\s*[:：]", text):
            return None

        # 无格式标记但有实质内容 → 当作最终回复
        if not re.search(r"Action\s*[:：]", text):
            if len(text.strip()) > 20:
                return None
            return False

        # Thought
        thought = ""
        thought_match = re.search(r"Thought\s*[:：]\s*(.*?)(?=Action\s*[:：]|\Z)", text, re.DOTALL)
        if thought_match:
            thought = thought_match.group(1).strip()

        # 工具名
        action_match = re.search(r"Action\s*[:：]\s*(\S+)", text)
        tool_name = action_match.group(1).strip() if action_match else ""
        if not tool_name:
            return False

        # 工具参数（JSON）
        tool_input = {}
        input_match = re.search(r"Action Input\s*[:：]\s*(\{.*)", text, re.DOTALL)
        if input_match:
            raw = input_match.group(1)
            # 找到最后一个 }，截取到那里
            last_brace = raw.rfind('}')
            if last_brace != -1:
                raw = raw[:last_brace + 1]
            try:
                tool_input = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning(f"Action Input JSON 解析失败: {e}")
                return False

        return AgentAction(
            tool=tool_name,
            tool_input=tool_input,
            thought=thought,
            log=text,
        )

    def _extract_final_answer(self, text: str) -> str:
        """从 LLM 输出中提取最终回复正文。"""
        for pattern in (r"Final Answer\s*[:：]\s*(.*)", r"最终答案\s*[:：]\s*(.*)"):
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        return text.strip()

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
            if tool_name == "execute_code" and "code" in tool_input:
                tool_input = {
                    **tool_input,
                    "code": prepare_code_for_sandbox(
                        tool_input["code"],
                        getattr(self, "_session_files", None) or [],
                    ),
                }
            result = tool.run(**tool_input)
            success = "[错误]" not in result and "[执行失败]" not in result
            return AgentObservation(tool=tool_name, result=result, success=success)
        except Exception as e:
            logger.error(f"工具 {tool_name} 执行异常: {e}")
            return AgentObservation(
                tool=tool_name,
                result=f"[错误] 工具执行异常: {str(e)}",
                success=False,
            )
