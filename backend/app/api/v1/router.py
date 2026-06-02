from fastapi import APIRouter

from .sessions import router as session_router
from .users import router as users_router
from .auth import router as auth_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(users_router)
v1_router.include_router(session_router)
v1_router.include_router(auth_router)
