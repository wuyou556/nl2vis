import asyncio
import logging
from collections.abc import AsyncGenerator

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

            # 获取必要配置
            settings = get_agent_config()
            update_sandbox_url(settings.sandbox_url)
            llm = create_llm_client(settings)
            tools = get_tools()
            memory = ConversationMemory()

            # 查历史消息
            history_result = await db.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(asc(Message.created_at))
                .limit(memory.max_messages)
            )
            history = history_result.scalars().all()
   
            # 组装AgentExecutor
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

    async def process_message_stream(self,session_id: int,user_content: str, db) -> AsyncGenerator[dict, None]:
        """流式处理用户消息"""
        final_output = None
        try:
            files_result = await db.execute(
                select(File).where(File.session_id == session_id)
            )
            files = files_result.scalars().all()

            # 获取必要配置
            settings = get_agent_config()
            update_sandbox_url(settings.sandbox_url)
            llm = create_llm_client(settings)
            tools = get_tools()
            memory = ConversationMemory()

            # 查历史消息
            history_result = await db.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(asc(Message.created_at))
                .limit(memory.max_messages)
            )
            history = history_result.scalars().all()

            # 组装AgentExecutor
            executor = AgentExecutor(
                llm_client=llm,
                tools=tools,
                memory=memory,
                settings=settings,
            )

            # 创建同步生成器
            def sync_generator():
                return executor.stream_run(
                    user_content,
                    session_id,
                    files,
                    history,
                )
            gen = sync_generator()

            # 接收传递tokens
            # 注意：StopIteration 不能在 asyncio.to_thread 中正确传播
            # 所以使用 iter() 和哨兵值来检测生成器结束
            SENTINEL = object()  # 哨兵值，标记生成器结束

            def safe_next():
                """安全的 next()，返回哨兵值代替抛出 StopIteration"""
                try:
                    return next(gen)
                except StopIteration:
                    return SENTINEL

            while True:
                event = await asyncio.to_thread(safe_next)
                if event is SENTINEL:
                    break
                yield event
                # 捕获最终结果
                if event.get("type") == "final":
                    final_output = event.get("output", "")

        except Exception as e:
            yield {"type": "error", "message": str(e)}
            final_output = f"抱歉，处理失败：{str(e)}"

        finally:
            # 无论成功失败，都把Agent回复入库
            if final_output is not None:
                await self._save_agent_message(session_id, final_output)

    async def _save_agent_message(self, session_id: int, content: str):
        """使用独立会话保存Agent回复到数据库"""
        from app.db.session import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            try:
                agent_message = Message(
                    session_id=session_id,
                    sender="agent",
                    content=content,
                )
                session.add(agent_message)
                await session.commit()
            except Exception as e:
                logger.error(f"保存Agent消息失败: {e}")
                await session.rollback()
            