import os

class Settings:
    #PostgreSQL
    DATABASE_URL = os.getenv("DATABASE_URL","postgresql+asyncpg://nl2vis:nl2vis@localhost:5432/nl2vis")

    #Redis	
    REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")		#缓存地址

    #沙箱
    SANDBOX_EXECUTOR_TIMEOUT = int(os.getenv("SANDBOX_EXECUTOR_TIMEOUT", "30"))  # 代码执行超时秒数
    SANDBOX_MAX_OUTPUT = int(os.getenv("SANDBOX_MAX_OUTPUT", "65536"))           # 输出最大字节数

    #应用
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"  # 开发/生产模式
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "").split(",")  # CORS 白名单

    #JWT
    JWT_SECRET = os.getenv("JWT_SECRET", "nl2vis-secret-key-2026")   # 签名密钥
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")              # 签名算法
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))  # token 过期时间(分钟)

settings = Settings()