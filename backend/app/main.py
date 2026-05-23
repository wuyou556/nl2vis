from dotenv import load_dotenv
from pathlib import Path
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 1) 统一加载根目录 .env（在导入其余模块前）
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists:
    load_dotenv(env_path)
    logging.info(f"Loaded env from {env_path}")
else:
    load_dotenv()
    logging.warning(f".env not found at {env_path}")

# 2) 创建 app
app = FastAPI(
    title="nl2vis backend",
    description="Natural Language to Visualization Backend API",
    version="1.0.0"
)

# 3) CORS 配置（根据环境区分）
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if DEBUG else ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"] if DEBUG else ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

if DEBUG:
    logging.info("CORS: Development mode - allowing all origins")
else:
    logging.info(f"CORS: Production mode - allowing {ALLOWED_ORIGINS}")
