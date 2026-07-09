"""
SmartLearner FastAPI 主入口
个性化学习与知识管理 Agent
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.upload import router as upload_router
from app.api.course import router as course_router
from app.api.paper import router as paper_router
from app.api.knowledge import router as knowledge_router
from app.api.learning import router as learning_router

# 创建 FastAPI 应用
app = FastAPI(
    title="SmartLearner",
    description="个性化学习与知识管理Agent",
    version="0.1.0",
)

# 配置 CORS 中间件（开发环境允许所有来源）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册所有路由
app.include_router(upload_router)
app.include_router(course_router)
app.include_router(paper_router)
app.include_router(knowledge_router)
app.include_router(learning_router)


@app.on_event("startup")
async def startup_event():
    """应用启动时创建必要的数据目录"""
    settings.ensure_directories()
    # 确保知识库文件目录存在
    kb_files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "kb_files")
    os.makedirs(kb_files_dir, exist_ok=True)


@app.get("/")
async def root():
    """根路径，返回 API 基本信息"""
    return {
        "message": "SmartLearner API",
        "docs": "/docs",
    }


@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "ok",
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
