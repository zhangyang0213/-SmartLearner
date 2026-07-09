"""
学习资源推荐器模块
基于学习主题、水平、学习风格和薄弱环节推荐个性化学习资源
支持跨领域推荐和资源排序
"""

import json
import re
import logging
from typing import List, Optional

from app.core.llm import LLMClient

logger = logging.getLogger(__name__)


class ResourceRecommender:
    """学习资源推荐器，基于多维度推荐个性化学习资源"""

    def __init__(self, llm: LLMClient = None):
        """
        初始化资源推荐器

        参数:
            llm: LLMClient实例
        """
        self.llm = llm

    def _call_llm(self, prompt: str) -> str:
        """调用LLM获取响应"""
        if not self.llm:
            return ""

        try:
            return self.llm.chat(messages=[{"role": "user", "content": prompt}])
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            return ""

    def _parse_json_from_llm(self, text: str) -> Optional[dict]:
        """从LLM输出中解析JSON"""
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1).strip())
            except json.JSONDecodeError:
                pass

        start_arr = text.find("[")
        end_arr = text.rfind("]")
        if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
            try:
                return json.loads(text[start_arr:end_arr + 1])
            except json.JSONDecodeError:
                pass

        start_obj = text.find("{")
        end_obj = text.rfind("}")
        if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
            try:
                return json.loads(text[start_obj:end_obj + 1])
            except json.JSONDecodeError:
                pass

        return None

    def recommend_for_topic(self, topic: str, level: str,
                            learning_style: str = "visual") -> List[dict]:
        """根据主题、水平和学习风格推荐资源"""
        style_map = {
            "visual": "视觉型（偏好图表、视频、思维导图）",
            "auditory": "听觉型（偏好播客、讲座、讨论）",
            "reading": "阅读型（偏好书籍、文章、文档）",
            "kinesthetic": "实践型（偏好动手实验、项目实战）",
        }
        style_desc = style_map.get(learning_style, "综合型")

        level_map = {
            "beginner": "初学者", "intermediate": "中级", "advanced": "高级",
            "初学者": "初学者", "中级": "中级", "高级": "高级"
        }
        level_desc = level_map.get(level, level)

        prompt = f"""你是一位学习资源推荐专家。请根据以下信息推荐最适合的学习资源。

学习主题：{topic}
学习水平：{level_desc}
学习风格：{style_desc}

请推荐5-8个学习资源，严格按照以下JSON格式输出：
[
    {{
        "title": "资源标题",
        "type": "book/course/video/article/paper/podcast/project",
        "url_guess": "可能的资源链接",
        "description": "资源简介",
        "why_recommended": "推荐理由",
        "estimated_time": "预计学习时长"
    }}
]

所有内容用中文。

JSON输出："""

        llm_response = self._call_llm(prompt)
        resources = self._parse_json_from_llm(llm_response)

        if isinstance(resources, list):
            for resource in resources:
                resource.setdefault("title", "未知资源")
                resource.setdefault("type", "article")
                resource.setdefault("url_guess", "")
                resource.setdefault("description", "")
                resource.setdefault("why_recommended", "")
                resource.setdefault("estimated_time", "")
            return resources

        return self._generate_fallback_recommendations(topic, level_desc, learning_style)

    def _generate_fallback_recommendations(self, topic: str, level: str,
                                           learning_style: str) -> List[dict]:
        """回退推荐"""
        return [
            {
                "title": f"{topic}{level}级教程",
                "type": "course",
                "url_guess": "",
                "description": f"适合{level}水平的{topic}学习教程",
                "why_recommended": f"适合{level}水平的{learning_style}型学习者",
                "estimated_time": "根据个人节奏调整"
            },
            {
                "title": f"{topic}官方文档",
                "type": "article",
                "url_guess": "",
                "description": "官方文档是最权威的参考来源",
                "why_recommended": "所有水平的学习者都应参考官方文档",
                "estimated_time": "持续参考"
            }
        ]

    def recommend_by_weakness(self, progress_data: dict) -> List[dict]:
        """根据学习进度中的薄弱环节推荐针对性资源"""
        weak_areas = progress_data.get("weak_areas", [])
        completion_percentage = progress_data.get("completion_percentage", 0)
        milestones = progress_data.get("milestones", [])

        low_completion_milestones = []
        for m in milestones:
            if m.get("completion", 0) < 50 and m.get("status") != "not_started":
                low_completion_milestones.append(m)

        if not low_completion_milestones and not weak_areas:
            prompt_suffix = "学习者目前进度良好。请推荐巩固提升和拓展类的资源。"
        else:
            weakness_desc = ""
            for m in low_completion_milestones:
                weakness_desc += f"\n- 里程碑 {m.get('id', '')}: 完成率 {m.get('completion', 0)}%"
            for area in weak_areas:
                weakness_desc += f"\n- 薄弱领域 {area.get('milestone_id', '')}: {area.get('reason', '')}"
            prompt_suffix = f"学习者存在以下薄弱环节：{weakness_desc}\n\n请针对这些薄弱环节推荐有针对性的补救资源。"

        prompt = f"""你是一位学习诊断和资源推荐专家。

当前完成率：{completion_percentage}%
{prompt_suffix}

请推荐4-6个针对性学习资源，严格按照以下JSON格式输出：
[
    {{
        "title": "资源标题",
        "type": "book/course/video/article/paper/project",
        "url_guess": "可能的资源链接",
        "description": "资源简介",
        "why_recommended": "为什么这个资源能帮助克服薄弱环节",
        "estimated_time": "预计学习时长"
    }}
]

所有内容用中文。

JSON输出："""

        llm_response = self._call_llm(prompt)
        resources = self._parse_json_from_llm(llm_response)

        if isinstance(resources, list):
            for resource in resources:
                resource.setdefault("title", "未知资源")
                resource.setdefault("type", "article")
                resource.setdefault("url_guess", "")
                resource.setdefault("description", "")
                resource.setdefault("why_recommended", "")
                resource.setdefault("estimated_time", "")
            return resources

        fallback = []
        if low_completion_milestones:
            for m in low_completion_milestones[:3]:
                fallback.append({
                    "title": f"里程碑 {m.get('id', '')} 补强教程",
                    "type": "course",
                    "url_guess": "",
                    "description": f"针对完成率仅{m.get('completion', 0)}%的里程碑进行重点突破",
                    "why_recommended": "直接针对薄弱环节",
                    "estimated_time": "1-2周"
                })

        if not fallback:
            fallback.append({
                "title": "综合巩固练习",
                "type": "project",
                "url_guess": "",
                "description": "通过综合性项目练习巩固所学知识",
                "why_recommended": "项目实战是检验和巩固学习效果的最佳方式",
                "estimated_time": "1周"
            })

        return fallback

    def recommend_cross_domain(self, knowledge_areas: List[str]) -> List[dict]:
        """推荐跨领域的交叉学科资源"""
        areas_text = "、".join(knowledge_areas) if knowledge_areas else "通用领域"

        cross_points = []
        if len(knowledge_areas) >= 2:
            for i in range(len(knowledge_areas)):
                for j in range(i + 1, len(knowledge_areas)):
                    cross_points.append(f"{knowledge_areas[i]} × {knowledge_areas[j]}")

        prompt = f"""你是一位跨学科学习资源推荐专家。

学习者的知识领域：{areas_text}

交叉领域方向：{', '.join(cross_points) if cross_points else '请自由发掘'}

请推荐5-8个跨领域学习资源，严格按照以下JSON格式输出：
[
    {{
        "title": "资源标题",
        "type": "book/course/video/article/paper/podcast",
        "url_guess": "可能的资源链接",
        "description": "资源简介",
        "why_recommended": "为什么跨领域学习对这个学习者有价值",
        "estimated_time": "预计学习时长"
    }}
]

所有内容用中文。

JSON输出："""

        llm_response = self._call_llm(prompt)
        resources = self._parse_json_from_llm(llm_response)

        if isinstance(resources, list):
            for resource in resources:
                resource.setdefault("title", "未知资源")
                resource.setdefault("type", "article")
                resource.setdefault("url_guess", "")
                resource.setdefault("description", "")
                resource.setdefault("why_recommended", "")
                resource.setdefault("estimated_time", "")
            return resources

        return [
            {
                "title": f"{areas_text}跨学科应用",
                "type": "book",
                "url_guess": "",
                "description": f"探索{areas_text}的交叉研究",
                "why_recommended": "拓展视野，发现知识的跨领域连接",
                "estimated_time": "1-2周"
            }
        ]

    def rank_resources(self, resources: List[dict], user_preferences: dict) -> List[dict]:
        """根据用户偏好和相关性对资源进行排序"""
        if not resources:
            return []

        preferred_types = user_preferences.get("preferred_types", [])
        difficulty = user_preferences.get("difficulty", "intermediate")
        time_available = user_preferences.get("time_available", "")
        interests = user_preferences.get("interests", [])

        difficulty_scores = {
            "beginner": 1, "初学者": 1,
            "intermediate": 2, "中级": 2,
            "advanced": 3, "高级": 3
        }
        target_difficulty = difficulty_scores.get(difficulty, 2)

        scored_resources = []
        for resource in resources:
            score = 0.0

            res_type = resource.get("type", "article")
            if preferred_types and res_type in preferred_types:
                score += 0.25
            elif not preferred_types:
                score += 0.15

            res_difficulty = resource.get("difficulty", difficulty)
            res_diff_score = difficulty_scores.get(res_difficulty, 2)
            diff_gap = abs(res_diff_score - target_difficulty)
            score += max(0, 1.0 - diff_gap * 0.3) * 0.25

            score += 0.15 * 0.5

            res_desc = (resource.get("description", "") + resource.get("title", "")).lower()
            if interests:
                matched = sum(1 for interest in interests if interest.lower() in res_desc)
                score += min(1.0, 0.3 + matched * 0.2) * 0.2
            else:
                score += 0.3 * 0.2

            why = resource.get("why_recommended", "")
            score += min(1.0, len(why) / 100) * 0.15 if why else 0.2 * 0.15

            ranked_resource = dict(resource)
            ranked_resource["ranking_score"] = round(score, 3)
            scored_resources.append(ranked_resource)

        scored_resources.sort(key=lambda x: x["ranking_score"], reverse=True)
        return scored_resources
