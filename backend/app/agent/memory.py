class ConversationMemory:
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens

    def load_history(self, messages):
        result = []
        for msg in messages:
            role = "assistant" if msg.sender == "agent" else msg.sender
            result.append({"role": role, "content": msg.content})
        return result

    def truncate(self,messages):
        kept = []
        total = 0
        for mes in reversed(messages):
            tokens = len(mes["content"])/2
            if total+tokens > self.max_tokens:
                break
            total = total + tokens
            kept.append(mes)

        return list(reversed(kept))
    
    def build_messages(self,system_prompt, history, user_message, agent_steps):
        prompt = []
        prompt.append({"role": "system", "content": system_prompt})
        prompt.extend(self.truncate(history))
        prompt.extend(agent_steps)
        prompt.append({"role": "user", "content": user_message})

        return prompt        
