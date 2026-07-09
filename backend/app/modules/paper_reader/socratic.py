"""
苏格拉底式提问引擎 - 通过层层递进的提问引导深度理解
涵盖澄清、假设探查、证据探查、视角转换、推论和元认知等六大提问维度
"""

from typing import List, Optional

from app.core.rag_engine import rag_engine
from app.core.llm import LLMClient


# 苏格拉底式提问系统提示词
SOCRATIC_SYSTEM_PROMPT = """你是一位采用苏格拉底教学法的学术导师。你通过精心设计的层层提问，引导学生深入思考和理解论文内容，而非直接给出答案。

你的提问遵循六大维度：
1. **澄清（Clarification）**：帮助明确概念和论点的含义
2. **假设探查（Probing Assumptions）**：审视论点背后的隐含假设
3. **证据探查（Probing Evidence）**：追问支持论点的证据和理由
4. **视角转换（Viewpoints/Perspectives）**：引导从不同角度审视问题
5. **推论（Implications）**：探索论点的延伸影响和后果
6. **元认知（Questions about the Question）**：反思问题本身的意义

你的教学风格：
- 循循善诱，从简单到复杂，层层递进
- 不急于给出答案，而是用问题启发思考
- 对学生的回答给予有针对性的反馈
- 在学生困惑时提供恰当的提示
- 鼓励批判性思维和独立思考
- 所有提问和反馈使用中文"""


# 苏格拉底提问维度详细指导
SOCRATIC_DIMENSIONS = {
    "澄清": {
        "purpose": "帮助明确概念和论点的确切含义",
    },
    "假设探查": {
        "purpose": "审视论点背后的隐含假设和前提条件",
    },
    "证据探查": {
        "purpose": "追问支持论点的证据质量和充分性",
    },
    "视角转换": {
        "purpose": "引导从不同角度审视同一问题",
    },
    "推论": {
        "purpose": "探索论点的延伸影响和逻辑后果",
    },
    "元认知": {
        "purpose": "反思问题本身的意义和提问方式",
    },
}


class SocraticQuestioner:
    """苏格拉底式提问引擎，通过递进式提问引导深度理解"""

    def __init__(self):
        """初始化苏格拉底提问引擎"""
        self.llm = LLMClient()

    def _retrieve_paper_content(
        self, knowledge_base_id: str, query: str = "", k: int = 10
    ) -> str:
        """从知识库中检索论文内容"""
        queries = [query] if query else []
        default_queries = [
            "核心论点 主要结论 研究发现",
            "研究方法 实验设计 数据分析",
            "理论框架 假设 模型 局限性",
        ]
        queries.extend(default_queries)

        all_contents = []
        seen_texts = set()

        for q in queries:
            sources = rag_engine.get_sources(
                knowledge_base_id=knowledge_base_id,
                question=q,
                k=k,
            )
            for src in sources:
                text = src.get("content", "")
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    all_contents.append(text)

        return "\n\n".join(all_contents)

    def generate_questions(
        self,
        knowledge_base_id: str,
        focus_area: Optional[str] = None,
    ) -> List[dict]:
        """
        生成苏格拉底式提问

        Args:
            knowledge_base_id: 知识库ID
            focus_area: 关注的重点领域

        Returns:
            苏格拉底式问题列表
        """
        context = self._retrieve_paper_content(knowledge_base_id, query=focus_area or "")

        focus_instruction = f"请重点关注论文中与「{focus_area}」相关的内容。" if focus_area else "请覆盖论文的各个方面。"

        dimensions_desc = "\n".join(
            f"- **{name}**：{info['purpose']}"
            for name, info in SOCRATIC_DIMENSIONS.items()
        )

        prompt = f"""请基于以下论文内容，生成一系列苏格拉底式的思考提问。

{focus_instruction}

## 苏格拉底提问的六大维度
{dimensions_desc}

## 论文内容
{context}

## 输出格式
请严格按照以下JSON格式输出：
```json
{{
  "questions": [
    {{
      "question": "具体的问题文本",
      "purpose": "这个问题的目的",
      "hint": "思考提示",
      "depth_level": 1
    }}
  ]
}}
```

生成8-12个问题，覆盖六大维度，深度等级1-3。"""

        messages = [
            {"role": "system", "content": SOCRATIC_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.5)

        questions = result.get("questions", [])
        if not questions and isinstance(result, list):
            questions = result

        for q in questions:
            if "depth_level" not in q or q["depth_level"] not in (1, 2, 3):
                q["depth_level"] = 2
            if "hint" not in q:
                q["hint"] = ""
            if "purpose" not in q:
                q["purpose"] = ""

        return questions

    def evaluate_response(
        self,
        knowledge_base_id: str,
        question: str,
        user_response: str,
    ) -> dict:
        """
        评估用户对苏格拉底提问的回答

        Args:
            knowledge_base_id: 知识库ID
            question: 苏格拉底提问
            user_response: 用户对该问题的回答

        Returns:
            评估结果字典
        """
        context = self._retrieve_paper_content(knowledge_base_id, query=question)

        prompt = f"""请评估学生对以下苏格拉底式提问的回答，并提供反馈和追问。

## 论文参考内容
{context}

## 提问
{question}

## 学生的回答
{user_response}

请严格按照以下JSON格式输出：
```json
{{
  "understanding_level": "surface",
  "feedback": "对学生回答的详细反馈",
  "follow_up_question": "一个追问",
  "key_points_missed": ["遗漏的关键要点1"]
}}
```

理解水平：surface/deep/insightful"""

        messages = [
            {"role": "system", "content": SOCRATIC_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.4)

        if "understanding_level" not in result or result["understanding_level"] not in (
            "surface", "deep", "insightful",
        ):
            result["understanding_level"] = "surface"
        if "feedback" not in result:
            result["feedback"] = ""
        if "follow_up_question" not in result:
            result["follow_up_question"] = ""
        if "key_points_missed" not in result:
            result["key_points_missed"] = []

        return result

    def generate_reading_guide(self, knowledge_base_id: str) -> dict:
        """
        生成导读计划

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            阅读指导字典
        """
        context = self._retrieve_paper_content(knowledge_base_id)

        prompt = f"""请为以下论文生成一份结构化的导读计划。

## 论文内容
{context}

请严格按照以下JSON格式输出：
```json
{{
  "prerequisites": ["前置知识1", "前置知识2"],
  "sections": [
    {{
      "title": "阅读部分标题",
      "key_questions": ["核心问题1", "核心问题2"],
      "reading_tips": "阅读建议"
    }}
  ],
  "post_reading_reflection": "读后反思引导"
}}
```"""

        messages = [
            {"role": "system", "content": SOCRATIC_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.4)

        if "prerequisites" not in result:
            result["prerequisites"] = []
        if "sections" not in result:
            result["sections"] = []
        if "post_reading_reflection" not in result:
            result["post_reading_reflection"] = ""

        for section in result["sections"]:
            if "title" not in section:
                section["title"] = ""
            if "key_questions" not in section:
                section["key_questions"] = []
            if "reading_tips" not in section:
                section["reading_tips"] = ""

        return result
