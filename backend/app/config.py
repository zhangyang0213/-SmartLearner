"""
SmartLearner 项目配置管理模块
使用 pydantic-settings 从环境变量和 .env 文件加载配置
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类，支持从 .env 文件和环境变量加载"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ===== 阿里百炼 DashScope API 配置 =====
    DASHSCOPE_API_KEY: str = Field(default="", description="阿里百炼API Key")
    DASHSCOPE_BASE_URL: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        description="DashScope OpenAI兼容API基础URL",
    )

    # ===== LLM 模型配置 =====
    LLM_MODEL: str = Field(default="qwen-plus", description="主用LLM模型名称")
    LLM_MODEL_FAST: str = Field(default="qwen-turbo", description="快速LLM模型名称")

    # ===== Embedding 模型配置 =====
    EMBEDDING_MODEL: str = Field(
        default="text-embedding-v3", description="嵌入模型名称"
    )
    EMBEDDING_DIMENSION: int = Field(
        default=1024, description="嵌入向量维度"
    )

    # ===== 向量存储配置 =====
    VECTOR_STORE_PATH: str = Field(
        default="./data/vector_store", description="FAISS向量存储路径"
    )

    # ===== 文件上传配置 =====
    UPLOAD_DIR: str = Field(default="./data/uploads", description="上传文件存储目录")

    # ===== 数据库配置 =====
    DATABASE_URL: str = Field(
        default="sqlite:///./data/smartlearner.db", description="数据库连接URL"
    )

    # ===== 阿里云 OSS 配置（可选） =====
    OSS_ACCESS_KEY_ID: str = Field(default="", description="阿里云OSS AccessKey ID")
    OSS_ACCESS_KEY_SECRET: str = Field(
        default="", description="阿里云OSS AccessKey Secret"
    )
    OSS_ENDPOINT: str = Field(default="", description="阿里云OSS Endpoint")
    OSS_BUCKET_NAME: str = Field(default="", description="阿里云OSS Bucket名称")

    # ===== 文档分块配置 =====
    CHUNK_SIZE: int = Field(default=500, description="文档分块大小（字符数）")
    CHUNK_OVERLAP: int = Field(default=50, description="文档分块重叠大小（字符数）")

    def ensure_directories(self) -> None:
        """确保必要的目录存在"""
        os.makedirs(self.VECTOR_STORE_PATH, exist_ok=True)
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        # 确保 SQLite 数据库的目录存在
        db_path = self.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)


# 全局配置单例
settings = Settings()
