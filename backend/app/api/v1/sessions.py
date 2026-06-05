import os
import uuid
from typing import Annotated
from datetime import datetime
from pathlib import Path as FilePath

from fastapi import APIRouter, Depends, HTTPException, Path, status, UploadFile
from sqlalchemy import select,desc,asc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.session import Session
from app.models.message import Message
from app.models.file import File
from app.models.user import User
from app.schemas.session import SessionResponse, SessionUpdate
from app.schemas.message import MessageCreate,MessageResponse
from app.schemas.file import FileResponse
from app.services import SessionService
from .auth import get_current_user

router = APIRouter(prefix="/sessions", tags=["会话管理"])
UPLOAD_DIR = FilePath(__file__).parent.parent.parent / "uploads"

# ---------------------------------------------------------------------------
# POST /sessions/  创建会话
# ---------------------------------------------------------------------------
@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    session = Session(user_id=current_user.id)
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session

# ---------------------------------------------------------------------------
# GET /sessions/ 查找会话列表
# ---------------------------------------------------------------------------
@router.get("/",response_model=list[SessionResponse])
async def get_sessions_list(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Session).where(Session.user_id == current_user.id).order_by(desc(Session.id)))
    session = result.scalars().all()
    return session

# ---------------------------------------------------------------------------
# GET /sessions/{session_id}  查单个会话
# ---------------------------------------------------------------------------
@router.get("/{session_id}",response_model=SessionResponse)
async def get_session(
    session_id: Annotated[int,Path(ge=1)],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="会话不存在")
    return session

# ---------------------------------------------------------------------------
# PUT /sessions/{session_id}  修改会话（改标题）
# ---------------------------------------------------------------------------
@router.put("/{session_id}",response_model = SessionResponse)
async def update_session(
    session_id: Annotated[int,Path(ge=1)],
    data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="会话不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key,value in update_data.items():
        setattr(session,key,value)
    await db.flush()
    await db.refresh(session)
    return session

# # ---------------------------------------------------------------------------
# # DELETE /sessions/{session_id}  关闭会话
# # ---------------------------------------------------------------------------
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def close_session(
    session_id: Annotated[int,Path(ge=1)],
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="会话不存在")
    session.status = "closed"
    session.ended_at = datetime.now()

    await db.flush()



# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/messages  查询所有消息
# ---------------------------------------------------------------------------
@router.get("/{session_id}/messages",response_model=list[MessageResponse])
async def get_messages_list(
    session_id: Annotated[int,Path(ge=1)],
    db: AsyncSession = Depends(get_db)
):
    # 发消息前确认会话存在
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")
    message = (await db.execute(select(Message).where(Message.session_id == session_id).order_by(asc(Message.created_at)))).scalars().all()
    return message

# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/messages  发送消息
# ---------------------------------------------------------------------------
@router.post("/{session_id}/messages",response_model=MessageResponse)
async def send_message(
    session_id: Annotated[int,Path(ge=1)],
    data: MessageCreate,
    db: AsyncSession = Depends(get_db)
):
    # 发消息前确认会话存在
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")

    # 存储消息到数据库
    message = Message(
        session_id=session_id,
        sender="user",
        content=data.content
    )
    db.add(message)
    await db.flush()
    await db.refresh(message)
    
    # 调用服务层处理消息获得回复
    agent_message = await SessionService().process_message(session_id, data.content, db)

    return agent_message



# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/files  查询文件列表
# ---------------------------------------------------------------------------
@router.get("/{session_id}/files", response_model=list[FileResponse])
async def get_files_list(
    session_id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")
    files = (await db.execute(
        select(File).where(File.session_id == session_id).order_by(asc(File.uploaded_at))
    )).scalars().all()
    return files


# ---------------------------------------------------------------------------
# GET /sessions/{session_id}/files/{file_id}  查单个文件
# ---------------------------------------------------------------------------
@router.get("/{session_id}/files/{file_id}", response_model=FileResponse)
async def get_file(
    session_id: Annotated[int, Path(ge=1)],
    file_id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")

    file = (await db.execute(
        select(File).where(File.id == file_id, File.session_id == session_id)
    )).scalars().first()
    if not file:
        raise HTTPException(404, detail="文件不存在")
    return file


# ---------------------------------------------------------------------------
# DELETE /sessions/{session_id}/files/{file_id}  删除文件
# ---------------------------------------------------------------------------
@router.delete("/{session_id}/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(
    session_id: Annotated[int, Path(ge=1)],
    file_id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(get_db),
):
    session = (await db.execute(select(Session).where(Session.id == session_id))).scalars().first()
    if not session:
        raise HTTPException(404, detail="会话不存在")

    file = (await db.execute(
        select(File).where(File.id == file_id, File.session_id == session_id)
    )).scalars().first()
    if not file:
        raise HTTPException(404, detail="文件不存在")

    await db.delete(file)
    await db.flush()

# ---------------------------------------------------------------------------
# POST /sessions/{session_id}/files  上传文件
# ---------------------------------------------------------------------------
@router.post("/{session_id}/files",response_model=FileResponse,status_code=status.HTTP_201_CREATED)
async def upload_files(
    file: UploadFile,
    session_id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(get_db)
):
    existing = (await db.execute(select(Session).where(Session.id == session_id))).scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404,detail="会话不存在")
    
    # 创建安全文件名
    ext = os.path.splitext(file.filename)[1]
    safe_name = f"{uuid.uuid4()}{ext}"
    session_dir = UPLOAD_DIR / str(session_id)
    session_dir.mkdir(parents=True,exist_ok=True)
    file_path = session_dir /safe_name

    # 写入磁盘
    contents = await file.read()
    file_path.write_bytes(contents)

    # 写入数据库
    file_record = File(
        session_id=session_id,
        filename=file.filename,
        storage_path=str(file_path),
        content_type=file.content_type,
        size=len(contents),
    )
    db.add(file_record)
    await db.flush()
    await db.refresh(file_record)
    return file_record