"""
论文阅读 API 路由
提供论文摘要、关键概念提取、方法论分析、苏格拉底式提问、文献推荐等功能
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.modules.paper_reader.summarizer import PaperSummarizer
from app.modules.paper_reader.socratic import SocraticQuestioner
from app.modules.paper_reader.recommender import LiteratureRecommender

router = APIRouter(prefix="/api/paper", tags=["论文阅读"])

# 实例化模块
summarizer = PaperSummarizer()
socratic = SocraticQuestioner()
recommender = LiteratureRecommender()


# ===== 请求模型 =====

class KbIdRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")


class SocraticQuestionsRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    focus_area: Optional[str] = Field(default=None, description="关注领域")


class SocraticEvaluateRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    question: str = Field(..., description="苏格拉底提问")
    user_response: str = Field(..., description="用户的回答")


class RecommendRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    num_results: int = Field(default=5, description="推荐数量")


# ===== 路由 =====

@router.post("/summarize")
async def summarize_paper(request: KbIdRequest):
    """生成论文全文摘要"""
    try:
        result = summarizer.summarize(knowledge_base_id=request.kb_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"论文摘要生成失败: {str(e)}")


@router.post("/quick-summary")
async def quick_summary(request: KbIdRequest):
    """快速摘要"""
    try:
        summary = summarizer.quick_summary(knowledge_base_id=request.kb_id)
        return {"summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"快速摘要生成失败: {str(e)}")


@router.post("/concepts")
async def extract_concepts(request: KbIdRequest):
    """提取关键概念"""
    try:
        concepts = summarizer.extract_key_concepts(knowledge_base_id=request.kb_id)
        return {"concepts": concepts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"概念提取失败: {str(e)}")


@router.post("/methodology")
async def extract_methodology(request: KbIdRequest):
    """提取方法论"""
    try:
        result = summarizer.extract_methodology(knowledge_base_id=request.kb_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"方法论提取失败: {str(e)}")


@router.post("/socratic/questions")
async def generate_socratic_questions(request: SocraticQuestionsRequest):
    """生成苏格拉底式提问"""
    try:
        questions = socratic.generate_questions(
            knowledge_base_id=request.kb_id,
            focus_area=request.focus_area,
        )
        return {"questions": questions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"苏格拉底提问生成失败: {str(e)}")


@router.post("/socratic/evaluate")
async def evaluate_socratic_response(request: SocraticEvaluateRequest):
    """评估苏格拉底式回答"""
    try:
        result = socratic.evaluate_response(
            knowledge_base_id=request.kb_id,
            question=request.question,
            user_response=request.user_response,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"回答评估失败: {str(e)}")


@router.post("/reading-guide")
async def generate_reading_guide(request: KbIdRequest):
    """生成论文导读"""
    try:
        result = socratic.generate_reading_guide(knowledge_base_id=request.kb_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导读生成失败: {str(e)}")


@router.post("/recommend")
async def recommend_literature(request: RecommendRequest):
    """推荐相关文献"""
    try:
        recommendations = recommender.recommend_related(
            knowledge_base_id=request.kb_id,
            num_results=request.num_results,
        )
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文献推荐失败: {str(e)}")


@router.post("/literature-map")
async def generate_literature_map(request: KbIdRequest):
    """生成文献图谱"""
    try:
        result = recommender.generate_literature_map(
            knowledge_base_id=request.kb_id,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文献图谱生成失败: {str(e)}")


@router.post("/contradicting-views")
async def find_contradicting_views(request: KbIdRequest):
    """发现反面观点"""
    try:
        views = recommender.find_contradicting_views(
            knowledge_base_id=request.kb_id,
        )
        return {"views": views}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"反面观点发现失败: {str(e)}")
