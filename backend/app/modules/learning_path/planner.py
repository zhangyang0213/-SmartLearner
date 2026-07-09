"""
学习路径规划器模块
使用LLM生成个性化学习计划、推荐资源和生成每日任务
"""

import json
import uuid
import os
import re
import logging
from datetime import datetime
from typing import List, Optional

from app.core.llm import LLMClient

logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data")


class LearningPathPlanner:
    """学习路径规划器，使用LLM作为专家学习路径设计师"""

    def __init__(self, llm: LLMClient = None, search_engine=None):
        """
        初始化学习路径规划器

        参数:
            llm: LLMClient实例
            search_engine: 搜索引擎实例
        """
        self.llm = llm
        self.search_engine = search_engine

    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM获取响应

        参数:
            prompt: 提示词

        返回:
            LLM响应文本
        """
        if not self.llm:
            return ""

        try:
            return self.llm.chat(messages=[{"role": "user", "content": prompt}])
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return ""

    def _call_llm_json(self, prompt: str, system_prompt: str = "") -> Optional[dict]:
        """
        调用LLM获取JSON响应

        参数:
            prompt: 提示词
            system_prompt: 系统提示词

        返回:
            解析后的字典，失败返回None
        """
        if not self.llm:
            return None

        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            return self.llm.chat_json(messages=messages, temperature=0.3)
        except Exception as e:
            logger.error(f"LLM JSON调用失败: {e}")
            return None

    def _parse_json_from_llm(self, text: str) -> Optional[dict]:
        """
        从LLM输出中解析JSON

        参数:
            text: LLM输出文本

        返回:
            解析出的字典，失败返回None
        """
        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从markdown代码块中提取
        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        # 尝试找到第一个{和最后一个}之间的内容
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        return None

    def create_learning_plan(self, goal: str, current_level: str, timeframe: str,
                             preferences: dict = None) -> dict:
        """
        生成结构化学习计划
        """
        preferences = preferences or {}

        style_desc = ""
        if preferences.get("learning_style"):
            style_desc = f"偏好学习风格：{preferences['learning_style']}"
        daily_time = preferences.get("daily_time", "1-2小时")

        prompt = f"""你是一位资深学习路径设计师，擅长为各类学习者制定个性化学习计划。请为以下学习需求制定一个详细的学习计划。

学习目标：{goal}
当前水平：{current_level}
计划时间范围：{timeframe}
{style_desc}
每日可用学习时间：{daily_time}

请生成一个结构化的学习计划，严格按照以下JSON格式输出（不要添加任何其他文字说明）：

{{
    "title": "学习计划标题",
    "milestones": [
        {{
            "id": "m1",
            "title": "里程碑标题",
            "description": "里程碑详细描述",
            "estimated_duration": "预计时长（如：2周）",
            "resources": [
                {{
                    "title": "资源标题",
                    "type": "book/course/video/article/paper",
                    "description": "资源简述"
                }}
            ],
            "prerequisites": ["前置条件1", "前置条件2"],
            "learning_objectives": ["学习目标1", "学习目标2"]
        }}
    ],
    "total_duration": "总时长",
    "difficulty_progression": "难度递进说明",
    "study_tips": "学习建议"
}}

要求：
1. 里程碑数量根据时间范围合理设置
2. 资源推荐要具体且可操作
3. 难度应循序渐进
4. 所有内容用中文

JSON输出："""

        llm_response = self._call_llm(prompt)
        plan_data = self._parse_json_from_llm(llm_response)

        if not plan_data:
            plan_data = self._generate_fallback_plan(goal, current_level, timeframe)

        plan_id = str(uuid.uuid4())

        for i, milestone in enumerate(plan_data.get("milestones", [])):
            if "id" not in milestone:
                milestone["id"] = f"m{i + 1}"

        result = {
            "plan_id": plan_id,
            "goal": goal,
            "current_level": current_level,
            "timeframe": timeframe,
            "milestones": plan_data.get("milestones", []),
            "total_duration": plan_data.get("total_duration", timeframe),
            "difficulty_progression": plan_data.get("difficulty_progression", "从基础到高级，逐步提升"),
            "created_at": datetime.now().isoformat(),
            "preferences": preferences
        }

        return result

    def _generate_fallback_plan(self, goal: str, current_level: str, timeframe: str) -> dict:
        """当LLM不可用时，生成基础回退计划"""
        time_mapping = {
            "1个月": 2, "1月": 2, "一个月": 2,
            "2个月": 3, "2月": 3, "两个月": 3,
            "3个月": 4, "3月": 4, "三个月": 4,
            "6个月": 6, "6月": 6, "半年": 6,
            "12个月": 8, "1年": 8, "一年": 8
        }

        milestone_count = 4
        for key, count in time_mapping.items():
            if key in timeframe:
                milestone_count = count
                break

        milestones = []
        stages = ["基础入门", "核心概念", "实践应用", "进阶提升", "项目实战", "综合巩固",
                  "深度探索", "专家之路"]

        for i in range(milestone_count):
            stage_name = stages[i] if i < len(stages) else f"阶段{i + 1}"
            milestones.append({
                "id": f"m{i + 1}",
                "title": f"{stage_name}：{goal}",
                "description": f"深入学习{goal}的{stage_name}阶段内容",
                "estimated_duration": f"约{timeframe}的第{i + 1}阶段",
                "resources": [
                    {
                        "title": f"{goal}{stage_name}推荐教程",
                        "type": "course",
                        "description": f"适合{current_level}水平的{goal}{stage_name}学习资源"
                    }
                ],
                "prerequisites": [f"完成阶段{i}"] if i > 0 else [],
                "learning_objectives": [
                    f"理解{goal}的{stage_name}核心概念",
                    f"能够应用{stage_name}相关知识解决实际问题"
                ]
            })

        return {
            "title": f"{goal}学习计划",
            "milestones": milestones,
            "total_duration": timeframe,
            "difficulty_progression": f"从{current_level}水平开始，逐步提升至更高水平",
            "study_tips": "建议每天保持稳定的学习节奏，理论与实践结合"
        }

    def refine_plan(self, plan: dict, feedback: str) -> dict:
        """根据用户反馈优化学习计划"""
        plan_json = json.dumps(plan, ensure_ascii=False, indent=2)

        prompt = f"""你是一位资深学习路径设计师。用户对当前学习计划提出了反馈，请根据反馈优化计划。

当前学习计划：
{plan_json}

用户反馈：{feedback}

严格按照以下JSON格式输出（不要添加任何其他文字说明）：
{{
    "milestones": [...],
    "total_duration": "...",
    "difficulty_progression": "...",
    "refinement_notes": "本次优化的说明"
}}

所有内容用中文。

JSON输出："""

        llm_response = self._call_llm(prompt)
        refined_data = self._parse_json_from_llm(llm_response)

        if refined_data:
            if "milestones" in refined_data:
                for i, milestone in enumerate(refined_data["milestones"]):
                    if "id" not in milestone:
                        milestone["id"] = f"m{i + 1}"
                plan["milestones"] = refined_data["milestones"]

            if "total_duration" in refined_data:
                plan["total_duration"] = refined_data["total_duration"]
            if "difficulty_progression" in refined_data:
                plan["difficulty_progression"] = refined_data["difficulty_progression"]

            plan["refinement_notes"] = refined_data.get("refinement_notes", feedback)
        else:
            plan["refinement_notes"] = f"用户反馈：{feedback}（自动优化未能完成，请手动调整）"

        plan["updated_at"] = datetime.now().isoformat()
        return plan

    def suggest_resources(self, topic: str, level: str) -> List[dict]:
        """为特定主题和水平推荐学习资源"""
        prompt = f"""你是一位学习资源推荐专家。请为以下学习主题推荐高质量的学习资源。

学习主题：{topic}
学习水平：{level}

请推荐5-8个学习资源，严格按照以下JSON格式输出（不要添加任何其他文字说明）：
[
    {{
        "title": "资源标题",
        "type": "book/course/video/article/paper",
        "description": "资源简介（2-3句话描述内容和适用场景）",
        "difficulty": "beginner/intermediate/advanced",
        "relevance_score": 0.95
    }}
]

要求：
1. 资源类型要多样化
2. 难度要匹配{level}水平
3. relevance_score在0.5-1.0之间
4. 所有内容用中文

JSON输出："""

        llm_response = self._call_llm(prompt)
        resources = self._parse_json_from_llm(llm_response)

        if isinstance(resources, list):
            for resource in resources:
                resource.setdefault("title", "未知资源")
                resource.setdefault("type", "article")
                resource.setdefault("description", "")
                resource.setdefault("difficulty", level)
                resource.setdefault("relevance_score", 0.7)
            return resources

        # 回退
        return [
            {
                "title": f"{topic}入门教程",
                "type": "course",
                "description": f"适合{level}水平的{topic}学习教程",
                "difficulty": level,
                "relevance_score": 0.8
            },
            {
                "title": f"{topic}实践指南",
                "type": "book",
                "description": f"系统讲解{topic}的实用技能",
                "difficulty": level,
                "relevance_score": 0.75
            }
        ]

    def generate_daily_tasks(self, plan: dict, date: str) -> List[dict]:
        """根据学习计划生成每日学习任务"""
        goal = plan.get("goal", "学习")
        milestones = plan.get("milestones", [])
        current_level = plan.get("current_level", "中级")

        milestones_summary = ""
        for m in milestones:
            milestones_summary += f"\n- {m.get('title', '')}: {m.get('description', '')[:100]}"

        prompt = f"""你是一位学习规划专家。请根据以下学习计划，为指定日期生成具体的学习任务。

学习目标：{goal}
当前水平：{current_level}
日期：{date}

学习计划里程碑：
{milestones_summary if milestones_summary else "暂无里程碑"}

请生成4-6个具体的学习任务，严格按照以下JSON格式输出：
[
    {{
        "title": "任务标题",
        "description": "任务详细描述",
        "duration_minutes": 30,
        "resource_links": ["相关资源链接或参考"],
        "completion_criteria": "完成标准"
    }}
]

要求：
1. 任务要具体可执行
2. 每个任务时长合理（15-90分钟）
3. 所有内容用中文

JSON输出："""

        llm_response = self._call_llm(prompt)
        tasks = self._parse_json_from_llm(llm_response)

        if isinstance(tasks, list):
            for task in tasks:
                task.setdefault("title", "学习任务")
                task.setdefault("description", "")
                task.setdefault("duration_minutes", 30)
                task.setdefault("resource_links", [])
                task.setdefault("completion_criteria", "完成相关学习内容")
            return tasks

        return [
            {
                "title": f"复习{goal}核心概念",
                "description": f"回顾和巩固{goal}的核心概念",
                "duration_minutes": 30,
                "resource_links": [],
                "completion_criteria": "能够用自己的语言复述核心概念"
            },
            {
                "title": f"{goal}实践练习",
                "description": f"通过动手实践加深对{goal}的理解",
                "duration_minutes": 45,
                "resource_links": [],
                "completion_criteria": "完成练习项目"
            }
        ]
