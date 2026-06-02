from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserUpdate, UserResponse
from app.api.v1.auth import get_current_user, hash_password

router = APIRouter(prefix="/users", tags=["用户管理"])

# ---------------------------------------------------------------------------
# GET /users/{user_id}  查单个用户
# ---------------------------------------------------------------------------
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: Annotated[int, Path(ge=1, description="用户ID")],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")
    return user


# ---------------------------------------------------------------------------
# PUT /users/{user_id}  更新用户
# ---------------------------------------------------------------------------
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: Annotated[int, Path(ge=1)],
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # model_dump(exclude_unset=True) 只包含用户实际传了的字段
    update_dict = data.model_dump(exclude_unset=True)

    # 如果传了 password，转为 hashed_password
    if "password" in update_dict:
        update_dict["hashed_password"] = hash_password(update_dict.pop("password"))

    for field, value in update_dict.items():
        setattr(user, field, value)

    await db.flush()
    await db.refresh(user)
    return user


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}  软删除
# ---------------------------------------------------------------------------
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: Annotated[int, Path(ge=1)],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    user.is_active = False
    await db.flush()
    # 204 No Content：不需要 return，FastAPI 自动返回空响应体

# ---------------------------------------------------------------------------
# GET /users  查询user表
# ---------------------------------------------------------------------------
@router.get("/", response_model=list[UserResponse])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(User).order_by(User.id))
    return result.scalars().all()