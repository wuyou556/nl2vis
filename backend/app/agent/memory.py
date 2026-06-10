import tiktoken
import functools
import os

from app.core.config import settings

class ConversationMemory:
    def __init__(self, max_tokens: int = None, max_messages: int = None):
        self.max_tokens = max_tokens or settings.MEMORY_MAX_TOKENS
        self.max_messages = max_messages or settings.MEMORY_MAX_MESSAGES

    def load_history(self, messages):
        result = []
        for msg in messages:
            role = "assistant" if msg.sender == "agent" else msg.sender
            result.append({"role": role, "content": msg.content})
        return result

    @staticmethod
    @functools.lru_cache(maxsize=1)
    def _get_encoding():
        model_name = os.getenv("LLM_MODEL_NAME","gpt-4")
        try:
            return tiktoken.encoding_for_model(model_name)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def _calculate_score(self, message: dict, filenames: list[str], position: int, total: int) -> float:
        """ 计算消息重要性 """
        score = 0.0
        role = message["role"]
        content = message["content"].lower()

        # 含有文件名加十分
        if any(fn.lower() in content for fn in filenames):
            score += 10

        # 含有关键词加五分
        if any(kw in content for kw in ["分析", "统计", "可视化", "画图", "趋势", "对比"]):
            score += 5
        
        # 用户发送加分
        if role == "user":
            score += 3

        # 消息重要性随时间线性衰减
        score += (position / total) * 5

        return score

    def truncate(self,messages,filenames):
        # 按分数排序
        score_messages = []
        for index, msg in enumerate(messages):
            score = self._calculate_score(msg, filenames, index, len(messages))
            score_messages.append({
                "score": score,
                "message": msg,
                "original_index": index
            }) 
        score_messages.sort(key=lambda x: x["score"], reverse=True)

        # 截取历史消息
        kept = []
        total = 0
        enc = self._get_encoding()
        for msg in score_messages:
            tokens = len(enc.encode(msg["message"]["content"]))
            if total+tokens > self.max_tokens:
                continue
            total = total + tokens
            kept.append(msg)
        kept.sort(key=lambda x:x["original_index"])

        return list(item["message"] for item in kept)
    
    def build_messages(self,system_prompt, history, user_message, agent_steps, filenames):
        prompt = []
        prompt.append({"role": "system", "content": system_prompt})
        prompt.extend(self.truncate(history,filenames))
        prompt.extend(agent_steps)
        prompt.append({"role": "user", "content": user_message})

        return prompt        
