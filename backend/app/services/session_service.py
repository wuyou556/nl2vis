import asyncio
import logging

from sqlalchemy import select, asc

from app.models.message import Message
from app.models.file import File
from app.agent import (
    AgentExecutor,
    get_agent_config,
    create_llm_client,
    ConversationMemory,
    get_tools,
)
from app.agent.tools import update_sandbox_url

logger = logging.getLogger(__name__)

class SessionService:
    async def process_message(self, session_id: int, user_content: str, db) -> Message:
        """ 服务层核心 """
        try:
            # 查文件
            files_result = await db.execute(
                select(File).where(File.session_id == session_id)
            )
            files = files_result.scalars().all()

            # 查历史消息
            history_result = await db.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(asc(Message.created_at))
            )
            history = history_result.scalars().all()
            
            # 组装AgentExecutor
            settings = get_agent_config()
            update_sandbox_url(settings.sandbox_url)
            llm = create_llm_client(settings)
            tools = get_tools()
            memory = ConversationMemory()

            executor = AgentExecutor(
                llm_client=llm,
                tools=tools,
                memory=memory,
                settings=settings,
            )

            result = await asyncio.to_thread(
                executor.run,
                user_content,
                session_id,
                files,
                history,
            )

            agent_message = Message(
                session_id=session_id,
                sender="agent",
                content=result.output,
            )
            db.add(agent_message)
            await db.flush()
            await db.refresh(agent_message)
            return agent_message
        except Exception as e:
            logger.error(f"Agent 处理失败：{e}")
            error_message = Message(
                session_id=session_id,
                sender="system",
                content=f"抱歉，处理你的请求时出了点问题：{str(e)}",
            )
            db.add(error_message)
            await db.flush()
            await db.refresh(error_message)
            return error_message

