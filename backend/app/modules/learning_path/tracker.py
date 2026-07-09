"""
学习进度追踪器模块
记录和追踪学习进度、学习时长和学习统计
使用JSON文件存储进度数据
"""

import json
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.llm import LLMClient

logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data")
PROGRESS_FILE = os.path.join(DATA_DIR, "learning_progress.json")


class LearningProgressTracker:
    """学习进度追踪器，记录学习进度、统计学习数据并提供建议"""

    def __init__(self, llm: LLMClient = None):
        """
        初始化学习进度追踪器

        参数:
            llm: LLMClient实例
        """
        self.llm = llm
        os.makedirs(DATA_DIR, exist_ok=True)
        self._ensure_store_file()

    def _ensure_store_file(self):
        """确保进度存储文件存在"""
        if not os.path.exists(PROGRESS_FILE):
            with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
                json.dump({"plans": {}}, f, ensure_ascii=False, indent=2)

    def _load_store(self) -> dict:
        """从JSON文件加载进度数据"""
        self._ensure_store_file()
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_store(self, data: dict):
        """将进度数据保存到JSON文件"""
        os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _call_llm(self, prompt: str) -> str:
        """调用LLM获取响应"""
        if not self.llm:
            return ""

        try:
            return self.llm.chat(messages=[{"role": "user", "content": prompt}])
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return ""

    def _ensure_plan_structure(self, store: dict, plan_id: str) -> dict:
        """确保计划数据结构完整"""
        if plan_id not in store["plans"]:
            store["plans"][plan_id] = {
                "plan_id": plan_id,
                "created_at": datetime.now().isoformat(),
                "milestones": {},
                "study_sessions": [],
                "streak": {
                    "current_streak": 0,
                    "longest_streak": 0,
                    "last_study_date": None
                }
            }
        return store["plans"][plan_id]

    def _ensure_milestone_structure(self, plan_data: dict, milestone_id: str) -> dict:
        """确保里程碑数据结构完整"""
        if milestone_id not in plan_data["milestones"]:
            plan_data["milestones"][milestone_id] = {
                "milestone_id": milestone_id,
                "status": "not_started",
                "started_at": None,
                "completed_at": None,
                "tasks": {}
            }
        return plan_data["milestones"][milestone_id]

    def _ensure_task_structure(self, milestone_data: dict, task_id: str) -> dict:
        """确保任务数据结构完整"""
        if task_id not in milestone_data["tasks"]:
            milestone_data["tasks"][task_id] = {
                "task_id": task_id,
                "status": "not_started",
                "notes": "",
                "started_at": None,
                "completed_at": None,
                "updated_at": None
            }
        return milestone_data["tasks"][task_id]

    def _update_streak(self, plan_data: dict) -> dict:
        """更新学习连续天数"""
        today = datetime.now().strftime("%Y-%m-%d")
        streak = plan_data.get("streak", {
            "current_streak": 0,
            "longest_streak": 0,
            "last_study_date": None
        })

        last_study_date = streak.get("last_study_date")

        if last_study_date == today:
            pass
        elif last_study_date:
            last_date = datetime.strptime(last_study_date, "%Y-%m-%d")
            today_date = datetime.strptime(today, "%Y-%m-%d")
            diff = (today_date - last_date).days

            if diff == 1:
                streak["current_streak"] += 1
            elif diff > 1:
                streak["current_streak"] = 1
        else:
            streak["current_streak"] = 1

        streak["last_study_date"] = today
        if streak["current_streak"] > streak.get("longest_streak", 0):
            streak["longest_streak"] = streak["current_streak"]

        plan_data["streak"] = streak
        return streak

    def update_progress(self, plan_id: str, milestone_id: str, task_id: str,
                        status: str, notes: str = "") -> dict:
        """更新学习进度"""
        valid_statuses = {"not_started", "in_progress", "completed", "skipped"}
        if status not in valid_statuses:
            raise ValueError(f"无效的任务状态: {status}，有效值为: {valid_statuses}")

        store = self._load_store()
        plan_data = self._ensure_plan_structure(store, plan_id)
        milestone_data = self._ensure_milestone_structure(plan_data, milestone_id)
        task_data = self._ensure_task_structure(milestone_data, task_id)

        now = datetime.now().isoformat()

        task_data["status"] = status
        task_data["notes"] = notes
        task_data["updated_at"] = now

        if status == "in_progress" and not task_data.get("started_at"):
            task_data["started_at"] = now
        elif status == "completed":
            task_data["completed_at"] = now
            if not task_data.get("started_at"):
                task_data["started_at"] = now

        self._update_milestone_status(milestone_data)

        if status in ("completed", "in_progress"):
            self._update_streak(plan_data)

        self._save_store(store)

        return {
            "plan_id": plan_id,
            "milestone_id": milestone_id,
            "task_id": task_id,
            "status": status,
            "notes": notes,
            "updated_at": now
        }

    def _update_milestone_status(self, milestone_data: dict):
        """根据任务状态自动更新里程碑状态"""
        tasks = milestone_data.get("tasks", {})
        if not tasks:
            return

        task_statuses = [t["status"] for t in tasks.values()]

        if all(s == "completed" for s in task_statuses):
            milestone_data["status"] = "completed"
            milestone_data["completed_at"] = datetime.now().isoformat()
        elif any(s in ("in_progress", "completed") for s in task_statuses):
            milestone_data["status"] = "in_progress"
            if not milestone_data.get("started_at"):
                milestone_data["started_at"] = datetime.now().isoformat()
        else:
            milestone_data["status"] = "not_started"

    def get_progress(self, plan_id: str) -> dict:
        """获取学习计划的整体进度"""
        store = self._load_store()
        plan_data = store["plans"].get(plan_id)

        if not plan_data:
            return {
                "plan_id": plan_id,
                "completion_percentage": 0.0,
                "milestones": [],
                "streak_days": 0,
                "total_study_hours": 0.0
            }

        milestones_progress = []
        total_tasks = 0
        completed_tasks = 0

        for m_id, m_data in plan_data.get("milestones", {}).items():
            tasks = m_data.get("tasks", {})
            m_total = len(tasks)
            m_completed = sum(1 for t in tasks.values() if t["status"] == "completed")
            m_in_progress = sum(1 for t in tasks.values() if t["status"] == "in_progress")

            m_completion = round(m_completed / m_total * 100, 1) if m_total > 0 else 0.0

            total_tasks += m_total
            completed_tasks += m_completed

            task_list = []
            for t_id, t_data in tasks.items():
                task_list.append({
                    "task_id": t_id,
                    "title": t_data.get("title", t_id),
                    "description": t_data.get("description", ""),
                    "estimated_hours": t_data.get("estimated_hours", 2),
                    "status": t_data.get("status", "not_started"),
                    "notes": t_data.get("notes", ""),
                    "updated_at": t_data.get("updated_at")
                })

            milestones_progress.append({
                "id": m_id,
                "title": m_data.get("title", m_id),
                "description": m_data.get("description", ""),
                "order": m_data.get("order", 0),
                "estimated_duration": m_data.get("estimated_duration", ""),
                "status": m_data.get("status", "not_started"),
                "completion": m_completion,
                "total_tasks": m_total,
                "completed_tasks": m_completed,
                "in_progress_tasks": m_in_progress,
                "tasks": task_list
            })

        completion_percentage = round(completed_tasks / total_tasks * 100, 1) if total_tasks > 0 else 0.0

        total_study_minutes = sum(
            session.get("duration_minutes", 0)
            for session in plan_data.get("study_sessions", [])
        )
        total_study_hours = round(total_study_minutes / 60, 1)

        streak_days = plan_data.get("streak", {}).get("current_streak", 0)

        return {
            "plan_id": plan_id,
            "goal": plan_data.get("goal", ""),
            "completion_percentage": completion_percentage,
            "milestones": milestones_progress,
            "streak_days": streak_days,
            "total_study_hours": total_study_hours
        }

    def get_study_stats(self, plan_id: str, period: str = "week") -> dict:
        """获取指定时间段的学习统计"""
        store = self._load_store()
        plan_data = store["plans"].get(plan_id, {})

        now = datetime.now()
        if period == "day":
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "week":
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "month":
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=7)
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

        start_date_str = start_date.isoformat()

        sessions = plan_data.get("study_sessions", [])
        filtered_sessions = []
        for session in sessions:
            session_date = session.get("date", session.get("started_at", ""))
            if session_date and session_date >= start_date_str:
                filtered_sessions.append(session)

        total_minutes = sum(s.get("duration_minutes", 0) for s in filtered_sessions)
        total_hours = round(total_minutes / 60, 1)

        topics_studied = list(set(
            s.get("topic", "未分类") for s in filtered_sessions if s.get("topic")
        ))

        quizzes = [s for s in filtered_sessions if s.get("quiz_score") is not None]
        quizzes_taken = len(quizzes)
        avg_quiz_score = round(sum(q["quiz_score"] for q in quizzes) / quizzes_taken, 1) if quizzes_taken > 0 else 0.0

        time_distribution = {}
        for session in filtered_sessions:
            session_date = session.get("date", session.get("started_at", ""))[:10]
            duration = session.get("duration_minutes", 0)
            if session_date:
                time_distribution[session_date] = time_distribution.get(session_date, 0) + duration

        time_distribution_hours = {k: round(v / 60, 1) for k, v in time_distribution.items()}

        return {
            "total_hours": total_hours,
            "total_minutes": total_minutes,
            "topics_studied": topics_studied,
            "quizzes_taken": quizzes_taken,
            "avg_quiz_score": avg_quiz_score,
            "time_distribution": time_distribution_hours,
            "period": period,
            "sessions_count": len(filtered_sessions)
        }

    def record_study_session(self, plan_id: str, duration_minutes: int,
                             topic: str = "", notes: str = "") -> dict:
        """记录一次学习会话"""
        if duration_minutes <= 0:
            raise ValueError(f"学习时长必须大于0，当前值: {duration_minutes}")

        store = self._load_store()
        plan_data = self._ensure_plan_structure(store, plan_id)

        now = datetime.now()
        session_id = str(uuid.uuid4())

        session = {
            "session_id": session_id,
            "date": now.strftime("%Y-%m-%d"),
            "started_at": now.isoformat(),
            "duration_minutes": duration_minutes,
            "topic": topic,
            "notes": notes
        }

        if "study_sessions" not in plan_data:
            plan_data["study_sessions"] = []
        plan_data["study_sessions"].append(session)

        self._update_streak(plan_data)

        self._save_store(store)

        return {
            "session_id": session_id,
            "plan_id": plan_id,
            "duration_minutes": duration_minutes,
            "topic": topic,
            "date": now.strftime("%Y-%m-%d"),
            "recorded_at": now.isoformat()
        }

    def get_recommendations(self, plan_id: str) -> dict:
        """根据学习进度给出下一步学习建议"""
        store = self._load_store()
        plan_data = store["plans"].get(plan_id)

        if not plan_data:
            return {
                "next_milestone": None,
                "suggested_focus": "请先开始学习计划",
                "weak_areas": [],
                "motivational_message": "千里之行，始于足下！"
            }

        milestones = plan_data.get("milestones", {})
        sessions = plan_data.get("study_sessions", [])
        streak = plan_data.get("streak", {})

        next_milestone = None
        current_milestone = None

        for m_id, m_data in milestones.items():
            status = m_data.get("status", "not_started")
            if status == "in_progress":
                current_milestone = m_id
            elif status == "not_started" and next_milestone is None:
                next_milestone = m_id

        suggested_milestone = current_milestone or next_milestone

        weak_areas = []
        for m_id, m_data in milestones.items():
            tasks = m_data.get("tasks", {})
            if tasks:
                total = len(tasks)
                completed = sum(1 for t in tasks.values() if t["status"] == "completed")
                skipped = sum(1 for t in tasks.values() if t["status"] == "skipped")
                if skipped > 0 and total > 0:
                    weak_areas.append({
                        "milestone_id": m_id,
                        "skipped_tasks": skipped,
                        "completion_rate": round(completed / total * 100, 1),
                        "reason": f"有{skipped}个任务被跳过"
                    })

        recent_sessions = sessions[-7:] if len(sessions) >= 7 else sessions
        recent_minutes = sum(s.get("duration_minutes", 0) for s in recent_sessions)
        avg_daily_minutes = recent_minutes / 7 if recent_sessions else 0

        motivational_message = ""
        suggested_focus = ""

        if self.llm:
            try:
                progress = self.get_progress(plan_id)
                recent_topics = [s.get("topic", "") for s in recent_sessions if s.get("topic")]

                prompt = f"""你是一位学习教练和心理顾问。根据学习者的进度数据，给出个性化的学习建议和鼓励。

学习进度概要：
- 总完成率：{progress['completion_percentage']}%
- 连续学习天数：{progress['streak_days']}天
- 总学习时长：{progress['total_study_hours']}小时
- 最近学习主题：{', '.join(recent_topics[-5:]) if recent_topics else '暂无'}
- 日均学习时长：{round(avg_daily_minutes, 0)}分钟
- 薄弱领域：{json.dumps(weak_areas, ensure_ascii=False) if weak_areas else '暂无'}

请用中文给出以下内容：
1. 下一步学习重点建议（1-2句话）
2. 鼓励性的话语（1-2句话，温暖有力）

格式：
建议：[建议内容]
鼓励：[鼓励内容]"""

                llm_response = self._call_llm(prompt)
                if llm_response:
                    for line in llm_response.split("\n"):
                        line = line.strip()
                        if line.startswith("建议：") or line.startswith("建议:"):
                            suggested_focus = line.split("：", 1)[-1].split(":", 1)[-1].strip()
                        elif line.startswith("鼓励：") or line.startswith("鼓励:"):
                            motivational_message = line.split("：", 1)[-1].split(":", 1)[-1].strip()

            except Exception as e:
                logger.warning(f"LLM生成建议失败: {e}")

        if not suggested_focus:
            if avg_daily_minutes < 30:
                suggested_focus = "建议增加每日学习时间，至少保持30分钟的学习量"
            elif suggested_milestone:
                suggested_focus = f"继续推进当前学习进度，聚焦里程碑 {suggested_milestone}"
            else:
                suggested_focus = "保持当前学习节奏，稳步前进"

        if not motivational_message:
            current_streak = streak.get("current_streak", 0)
            if current_streak >= 7:
                motivational_message = f"连续学习{current_streak}天，太棒了！坚持就是胜利！"
            elif current_streak >= 3:
                motivational_message = f"连续学习{current_streak}天，继续保持！"
            else:
                motivational_message = "每一步学习都是成长，加油！"

        return {
            "next_milestone": suggested_milestone,
            "suggested_focus": suggested_focus,
            "weak_areas": weak_areas,
            "motivational_message": motivational_message
        }
