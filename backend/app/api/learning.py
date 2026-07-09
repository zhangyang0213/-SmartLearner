"""
学习路径 API 路由
提供学习计划创建与优化、资源推荐、进度追踪、学习统计等功能
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.llm import LLMClient
from app.modules.learning_path.planner import LearningPathPlanner
from app.modules.learning_path.tracker import LearningProgressTracker
from app.modules.learning_path.recommender import ResourceRecommender

router = APIRouter(prefix="/api/learning", tags=["学习路径"])

# 实例化模块
llm = LLMClient()
planner = LearningPathPlanner(llm=llm)
tracker = LearningProgressTracker(llm=llm)
resource_recommender = ResourceRecommender(llm=llm)


# ===== 请求模型 =====

class CreatePlanRequest(BaseModel):
    goal: str = Field(..., description="学习目标")
    current_level: str = Field(..., description="当前水平")
    timeframe: str = Field(..., description="学习时间范围")
    preferences: Optional[Dict] = Field(default=None, description="学习偏好")


class RefinePlanRequest(BaseModel):
    plan: dict = Field(..., description="当前学习计划")
    feedback: str = Field(..., description="优化反馈")


class ResourcesRequest(BaseModel):
    topic: str = Field(..., description="学习主题")
    level: str = Field(..., description="学习水平")


class DailyTasksRequest(BaseModel):
    plan: dict = Field(..., description="学习计划")
    date: str = Field(..., description="日期，如 2024-01-15")


class UpdateProgressRequest(BaseModel):
    plan_id: str = Field(..., description="计划ID")
    milestone_id: str = Field(..., description="里程碑ID")
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态: not_started/in_progress/completed/skipped")
    notes: str = Field(default="", description="学习笔记")


class StudySessionRequest(BaseModel):
    plan_id: str = Field(..., description="计划ID")
    duration_minutes: int = Field(..., gt=0, description="学习时长(分钟)")
    topic: str = Field(default="", description="学习主题")
    notes: str = Field(default="", description="学习笔记")


class CrossDomainRequest(BaseModel):
    knowledge_areas: List[str] = Field(..., description="知识领域列表")


# ===== 路由 =====

@router.post("/plan")
async def create_learning_plan(request: CreatePlanRequest):
    """
    创建学习计划

    根据学习目标、当前水平和时间范围生成个性化学习计划。
    """
    try:
        result = planner.create_learning_plan(
            goal=request.goal,
            current_level=request.current_level,
            timeframe=request.timeframe,
            preferences=request.preferences,
        )
        # 初始化 tracker 中的计划数据，存储 goal 和 milestones 以便 get_progress 能返回
        plan_id = result.get("plan_id", "")
        if plan_id:
            store = tracker._load_store()
            tracker._ensure_plan_structure(store, plan_id)
            store["plans"][plan_id]["goal"] = request.goal
            # 存储前端需要的完整里程碑数据
            milestones_data = {}
            for idx, m in enumerate(result.get("milestones", [])):
                m_id = m.get("id", f"m{idx + 1}")
                tasks_data = {}
                # 从 resources 或 learning_objectives 构建 tasks
                resources = m.get("resources", [])
                learning_objectives = m.get("learning_objectives", [])
                items = resources if resources else learning_objectives
                if not items:
                    items = [{"title": m.get("title", f"任务{idx+1}"), "description": m.get("description", "")}]
                for t_idx, r in enumerate(items):
                    t_id = f"{m_id}_t{t_idx + 1}"
                    t_title = r.get("title", r) if isinstance(r, dict) else str(r)
                    t_desc = r.get("description", "") if isinstance(r, dict) else ""
                    t_hours = 2  # 默认2小时
                    tasks_data[t_id] = {
                        "task_id": t_id,
                        "title": t_title,
                        "description": t_desc,
                        "estimated_hours": t_hours,
                        "status": "not_started",
                        "notes": "",
                        "started_at": None,
                        "completed_at": None,
                        "updated_at": None,
                    }
                milestones_data[m_id] = {
                    "milestone_id": m_id,
                    "title": m.get("title", ""),
                    "description": m.get("description", ""),
                    "order": idx,
                    "estimated_duration": m.get("estimated_duration", ""),
                    "status": "not_started",
                    "started_at": None,
                    "completed_at": None,
                    "tasks": tasks_data,
                }
            store["plans"][plan_id]["milestones"] = milestones_data
            tracker._save_store(store)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习计划创建失败: {str(e)}")


@router.post("/plan/refine")
async def refine_learning_plan(request: RefinePlanRequest):
    """
    优化学习计划

    根据用户反馈优化已有的学习计划。
    """
    try:
        result = planner.refine_plan(
            plan=request.plan,
            feedback=request.feedback,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习计划优化失败: {str(e)}")


@router.post("/resources")
async def suggest_resources(request: ResourcesRequest):
    """
    推荐学习资源

    根据学习主题和水平推荐适合的学习资源。
    """
    try:
        resources = planner.suggest_resources(
            topic=request.topic,
            level=request.level,
        )
        return {"resources": resources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"资源推荐失败: {str(e)}")


@router.post("/daily-tasks")
async def generate_daily_tasks(request: DailyTasksRequest):
    """
    生成每日学习任务

    根据学习计划为指定日期生成具体的学习任务。
    """
    try:
        tasks = planner.generate_daily_tasks(
            plan=request.plan,
            date=request.date,
        )
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"每日任务生成失败: {str(e)}")


@router.post("/progress/update")
async def update_progress(request: UpdateProgressRequest):
    """
    更新学习进度

    更新指定任务的学习状态和笔记。
    """
    try:
        result = tracker.update_progress(
            plan_id=request.plan_id,
            milestone_id=request.milestone_id,
            task_id=request.task_id,
            status=request.status,
            notes=request.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"进度更新失败: {str(e)}")


@router.get("/progress/{plan_id}")
async def get_progress(plan_id: str):
    """
    获取学习进度

    获取指定学习计划的整体进度，包括里程碑完成情况、学习时长等。
    """
    try:
        result = tracker.get_progress(plan_id=plan_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"进度获取失败: {str(e)}")


@router.post("/study-session")
async def record_study_session(request: StudySessionRequest):
    """
    记录学习会话

    记录一次学习活动的时长、主题和笔记。
    """
    try:
        result = tracker.record_study_session(
            plan_id=request.plan_id,
            duration_minutes=request.duration_minutes,
            topic=request.topic,
            notes=request.notes,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习会话记录失败: {str(e)}")


@router.get("/stats/{plan_id}")
async def get_study_stats(
    plan_id: str,
    period: str = Query(default="week", description="统计周期: day/week/month"),
):
    """
    获取学习统计

    获取指定时间段的学习统计数据，包括学习时长、主题分布等。
    """
    try:
        result = tracker.get_study_stats(plan_id=plan_id, period=period)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习统计获取失败: {str(e)}")


@router.get("/recommendations/{plan_id}")
async def get_recommendations(plan_id: str):
    """
    获取下一步学习建议

    根据学习进度给出下一步学习重点和鼓励。
    """
    try:
        result = tracker.get_recommendations(plan_id=plan_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"学习建议获取失败: {str(e)}")


@router.post("/recommend/cross-domain")
async def recommend_cross_domain(request: CrossDomainRequest):
    """
    跨领域资源推荐

    基于多个知识领域推荐交叉学科资源。
    """
    try:
        resources = resource_recommender.recommend_cross_domain(
            knowledge_areas=request.knowledge_areas,
        )
        return {"resources": resources}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"跨领域推荐失败: {str(e)}")
