"""
课程问答 API 路由
提供课程知识问答、多轮对话、测验生成与评估、流式问答等功能
"""

import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from app.core.rag_engine import rag_engine
from app.modules.course_qa.qa_engine import CourseQAEngine
from app.modules.course_qa.quiz_generator import QuizGenerator

router = APIRouter(prefix="/api/course", tags=["课程问答"])

# 实例化模块
qa_engine = CourseQAEngine()
quiz_generator = QuizGenerator()


# ===== 请求/响应模型 =====

class AskRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    question: str = Field(..., description="课程问题")


class ChatMessage(BaseModel):
    role: str = Field(..., description="角色: user 或 assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    question: str = Field(..., description="当前问题")
    history: List[ChatMessage] = Field(default_factory=list, description="历史对话")


class QuizGenerateRequest(BaseModel):
    kb_id: str = Field(..., description="知识库ID")
    topic: str = Field(..., description="测验主题")
    num_questions: int = Field(default=5, description="题目数量")
    difficulty: str = Field(default="medium", description="难度等级: easy/medium/hard")


class QuizEvaluateRequest(BaseModel):
    question: dict = Field(..., description="题目信息")
    user_answer: str = Field(..., description="用户答案")


# ===== 路由 =====

@router.post("/ask")
async def ask_course_question(request: AskRequest):
    """
    课程单轮问答

    根据知识库内容回答课程问题，返回答案、引用来源和置信度。
    """
    try:
        result = qa_engine.ask(
            knowledge_base_id=request.kb_id,
            question=request.question,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"问答失败: {str(e)}")


@router.post("/chat")
async def multi_turn_chat(request: ChatRequest):
    """
    多轮对话

    在历史对话上下文中进行课程问答，支持连续追问。
    """
    try:
        history = [msg.model_dump() for msg in request.history]
        result = qa_engine.multi_turn_chat(
            knowledge_base_id=request.kb_id,
            question=request.question,
            history=history,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"多轮对话失败: {str(e)}")


@router.post("/quiz/generate")
async def generate_quiz(request: QuizGenerateRequest):
    """
    生成测验

    根据主题和难度自动生成测验题目，基于布鲁姆分类法。
    """
    try:
        result = quiz_generator.generate_quiz(
            knowledge_base_id=request.kb_id,
            topic=request.topic,
            num_questions=request.num_questions,
            difficulty=request.difficulty,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测验生成失败: {str(e)}")


@router.post("/quiz/evaluate")
async def evaluate_quiz_answer(request: QuizEvaluateRequest):
    """
    评估测验答案

    对用户提交的测验答案进行评分和反馈。
    """
    try:
        result = quiz_generator.evaluate_answer(
            question=request.question,
            user_answer=request.user_answer,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"答案评估失败: {str(e)}")


@router.get("/stream/{kb_id}")
async def stream_qa(kb_id: str, q: str):
    """
    SSE 流式问答

    通过 Server-Sent Events 逐 token 返回问答结果，适合实时展示。
    """

    def event_generator():
        try:
            for token in rag_engine.streaming_query(kb_id, q):
                yield {"data": json.dumps({"token": token}, ensure_ascii=False)}
            yield {"data": json.dumps({"done": True}, ensure_ascii=False)}
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)}, ensure_ascii=False)}

    return EventSourceResponse(event_generator())
