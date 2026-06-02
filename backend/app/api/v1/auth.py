from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse,TokenResponse,LoginRequest

# 导入 + 路由初始化
router = APIRouter(prefix="/auth",tags=["用户认证"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Tokne 生成
def create_access_token(data: dict) -> str: 
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    return jwt.encode(to_encode,settings.JWT_SECRET,settings.JWT_ALGORITHM)

# 用户认证
async def get_current_user(
    token: Annotated[str,Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="登录过期,请重新登录",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        if not user_id:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = (await db.execute(select(User).where(user_id == User.id))).scalar_one_or_none()
    if not user:
        raise credentials_exception
    return user

def hash_password(password: str) -> str:
    """明文 → bcrypt 哈希"""
    return pwd_context.hash(password)

# 注册路由
@router.post("/register",response_model=TokenResponse)
async def register(
    data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(
        (User.username == data.username) | (User.email == data.email)
    )
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名或邮箱已被注册",
        )
    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    await db.flush()       # 触发 INSERT，拿到数据库生成的 id
    await db.refresh(user)  # 拿到数据库默认值 created_at / updated_at
    access_token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=access_token, token_type="bearer", user=user)

@router.post("/login",response_model=TokenResponse)
async def login(
    data: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码错误",
        headers={"WWW-Authenticate": "Bearer"}
    )
    user = (await db.execute(select(User).where(User.username == data.username))).scalar_one_or_none()
    if not user:
        raise credentials_exception
    if not pwd_context.verify(data.password, user.hashed_password):
        raise credentials_exception
    access_token = create_access_token({"user_id": user.id})
    return TokenResponse(access_token=access_token, token_type="bearer", user=user)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
