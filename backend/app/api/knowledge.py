"""
知识库管理 API 路由
提供知识库的创建、查询、删除、搜索和自然语言查询等功能
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.knowledge_base.manager import KnowledgeBaseManager
from app.modules.knowledge_base.search import HybridSearchEngine

router = APIRouter(prefix="/api/kb", tags=["知识库管理"])

# 实例化模块
kb_manager = KnowledgeBaseManager()
search_engine = HybridSearchEngine()


# ===== 请求模型 =====

class CreateKbRequest(BaseModel):
    name: str = Field(..., description="知识库名称")
    description: str = Field(..., description="知识库描述")
    category: str = Field(default="general", description="知识库分类")


class SearchRequest(BaseModel):
    query: str = Field(..., description="搜索查询")
    k: int = Field(default=5, description="返回结果数量")
    search_type: str = Field(default="hybrid", description="搜索类型: semantic/keyword/hybrid")


class MultiKbSearchRequest(BaseModel):
    kb_ids: List[str] = Field(..., description="知识库ID列表")
    query: str = Field(..., description="搜索查询")
    k: int = Field(default=5, description="返回结果数量")


class NlQueryRequest(BaseModel):
    query: str = Field(..., description="自然语言查询")


# ===== 路由 =====

@router.post("/create")
async def create_knowledge_base(request: CreateKbRequest):
    """创建知识库"""
    try:
        result = kb_manager.create_knowledge_base(
            name=request.name,
            description=request.description,
            category=request.category,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库创建失败: {str(e)}")


@router.get("/list")
async def list_knowledge_bases():
    """列出所有知识库"""
    try:
        result = kb_manager.list_knowledge_bases()
        return {"knowledge_bases": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库列表获取失败: {str(e)}")


@router.get("/{kb_id}")
async def get_knowledge_base(kb_id: str):
    """获取知识库详情"""
    try:
        result = kb_manager.get_knowledge_base(kb_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库查询失败: {str(e)}")


@router.delete("/{kb_id}")
async def delete_knowledge_base(kb_id: str):
    """删除知识库"""
    try:
        success = kb_manager.delete_knowledge_base(kb_id)
        return {"success": success}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"知识库删除失败: {str(e)}")


@router.get("/{kb_id}/stats")
async def get_kb_stats(kb_id: str):
    """获取知识库统计信息"""
    try:
        result = kb_manager.get_knowledge_base_stats(kb_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计信息获取失败: {str(e)}")


@router.post("/{kb_id}/search")
async def search_knowledge_base(kb_id: str, request: SearchRequest):
    """搜索知识库"""
    try:
        results = search_engine.search(
            kb_id=kb_id,
            query=request.query,
            k=request.k,
            search_type=request.search_type,
        )
        return {"results": results}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")


@router.post("/search/multi")
async def multi_kb_search(request: MultiKbSearchRequest):
    """跨知识库搜索"""
    try:
        results = search_engine.multi_kb_search(
            kb_ids=request.kb_ids,
            query=request.query,
            k=request.k,
        )
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"跨库搜索失败: {str(e)}")


@router.post("/{kb_id}/nl-query")
async def natural_language_query(kb_id: str, request: NlQueryRequest):
    """自然语言查询"""
    try:
        result = search_engine.natural_language_query(
            kb_id=kb_id,
            query=request.query,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"自然语言查询失败: {str(e)}")
