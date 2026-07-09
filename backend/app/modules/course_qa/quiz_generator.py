"""
测验生成器 - 基于布鲁姆分类法的智能测验生成模块
支持多难度等级、多题型的自动测验生成与评估
"""

import json
import uuid
from typing import List

from app.core.rag_engine import rag_engine
from app.core.llm import LLMClient


# 布鲁姆分类法等级定义
BLOOM_LEVELS = {
    1: "记忆（Remember）- 回忆事实和基本概念",
    2: "理解（Understand）- 解释和归纳概念",
    3: "应用（Apply）- 在新情境中使用知识",
    4: "分析（Analyze）- 分解并理解关系",
    5: "评价（Evaluate）- 基于标准做出判断",
    6: "创造（Create）- 产生新的或原创的作品",
}

# 难度等级与布鲁姆等级的映射
DIFFICULTY_BLOOM_MAP = {
    "easy": {
        "bloom_levels": [1, 2],
        "description": "基础难度，考察记忆与理解能力",
        "level_names": ["记忆", "理解"],
    },
    "medium": {
        "bloom_levels": [3, 4],
        "description": "中等难度，考察应用与分析能力",
        "level_names": ["应用", "分析"],
    },
    "hard": {
        "bloom_levels": [5, 6],
        "description": "高难度，考察评价与创造能力",
        "level_names": ["评价", "创造"],
    },
}

# 测验生成系统提示词
QUIZ_SYSTEM_PROMPT = """你是一位专业的课程测验设计专家，擅长根据布鲁姆分类法（Bloom's Taxonomy）设计高质量的测验题目。

你的设计原则：
1. 题目必须基于给定的课程内容，不能脱离材料凭空编造
2. 题目表述清晰明确，无歧义
3. 选项设计合理，干扰项有迷惑性但不具误导性
4. 解析要详细，帮助学生理解为什么正确答案是对的、其他选项为什么错
5. 严格按照指定的布鲁姆认知层次出题
6. 所有内容和输出使用中文"""

# 根据不同布鲁姆等级的出题提示
BLOOM_LEVEL_PROMPTS = {
    1: """请设计**记忆层次**的题目。这类题目考察学生回忆和识别已学知识的能力。
示例题型：事实性选择题、定义判断题
出题要点：
- 直接考察对概念定义、事实、术语的记忆
- 答案可在原文中直接找到对应内容
- 不需要推理或理解，只需准确回忆""",

    2: """请设计**理解层次**的题目。这类题目考察学生对知识的理解和解释能力。
示例题型：概念解释题、归纳总结题、对比选择题
出题要点：
- 要求用自己的话解释概念
- 需要理解概念的含义而非死记硬背
- 可能涉及简单的归纳和对比""",

    3: """请设计**应用层次**的题目。这类题目考察学生将知识应用到新情境的能力。
示例题型：案例分析题、计算应用题、情景选择题
出题要点：
- 提供新的情境或案例，要求学生应用所学知识解决
- 不是简单复述知识，而是要迁移运用
- 问题情境应与原文不同但原理相通""",

    4: """请设计**分析层次**的题目。这类题目考察学生分解和剖析知识结构的能力。
示例题型：关系分析题、结构拆解题、比较分析题
出题要点：
- 要求分析事物之间的关系、结构或组织
- 可能需要区分事实与观点、识别假设
- 需要比理解更深层的拆解和推理能力""",

    5: """请设计**评价层次**的题目。这类题目考察学生基于标准做出判断和评价的能力。
示例题型：论证评价题、方法评判题、观点评估题
出题要点：
- 要求对观点、方法或结论进行评价
- 需要基于特定标准做出判断
- 可能涉及对证据充分性、逻辑合理性的评估""",

    6: """请设计**创造层次**的题目。这类题目考察学生重新组织和创造的能力。
示例题型：方案设计题、观点构建题、创新应用题
出题要点：
- 要求综合多个要素创造新的方案或观点
- 需要将知识重组为新的结构或模式
- 是最高层次的认知活动，强调原创性和综合性""",
}


class QuizGenerator:
    """基于布鲁姆分类法的智能测验生成器"""

    def __init__(self):
        """初始化测验生成器"""
        self.llm = LLMClient()

    def _get_bloom_range(self, difficulty: str) -> List[int]:
        """根据难度等级获取布鲁姆等级范围"""
        if difficulty not in DIFFICULTY_BLOOM_MAP:
            raise ValueError(
                f"无效的难度等级: {difficulty}，可选值: {list(DIFFICULTY_BLOOM_MAP.keys())}"
            )
        return DIFFICULTY_BLOOM_MAP[difficulty]["bloom_levels"]

    def _build_quiz_prompt(
        self,
        topic: str,
        num_questions: int,
        difficulty: str,
        context: str,
        bloom_levels: List[int],
    ) -> str:
        """构建测验生成提示词"""

        bloom_descriptions = "\n".join(
            f"  - 等级{lvl}: {BLOOM_LEVELS[lvl]}" for lvl in bloom_levels
        )

        bloom_instructions = "\n\n".join(
            BLOOM_LEVEL_PROMPTS[lvl] for lvl in bloom_levels
        )

        prompt = f"""请根据以下课程内容，生成关于「{topic}」的测验题目。

## 要求
- 生成 {num_questions} 道题目
- 难度等级：{difficulty}（{DIFFICULTY_BLOOM_MAP[difficulty]['description']}）
- 涵盖的布鲁姆认知层次：
{bloom_descriptions}

## 各布鲁姆层次的出题指导
{bloom_instructions}

## 课程内容
{context}

## 输出格式
请严格按照以下JSON格式输出，不要添加任何其他内容：
```json
{{
  "title": "测验标题",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice",
      "question_text": "题目文本",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct_answer": "选项A",
      "explanation": "详细解析",
      "bloom_level": 1,
      "difficulty": "{difficulty}"
    }}
  ]
}}
```

## 题型说明
- multiple_choice: 单项选择题，必须包含4个选项
- true_false: 判断题，options为["正确", "错误"]
- short_answer: 简答题，options为空列表
- essay: 论述题，options为空列表

请确保题目的布鲁姆等级在 {bloom_levels} 范围内，题型分布合理。"""

        return prompt

    def generate_quiz(
        self,
        knowledge_base_id: str,
        topic: str,
        num_questions: int = 5,
        difficulty: str = "medium",
    ) -> dict:
        """
        生成测验：根据主题和难度自动生成测验题目

        Args:
            knowledge_base_id: 知识库ID
            topic: 测验主题
            num_questions: 题目数量，默认5道
            difficulty: 难度等级，可选 easy/medium/hard

        Returns:
            测验字典
        """
        # 获取布鲁姆等级范围
        bloom_levels = self._get_bloom_range(difficulty)

        # 从知识库检索相关内容
        sources = rag_engine.get_sources(
            knowledge_base_id=knowledge_base_id,
            question=topic,
            k=10,
        )
        context = "\n\n".join([src.get("content", "") for src in sources])

        # 构建提示词
        prompt = self._build_quiz_prompt(
            topic=topic,
            num_questions=num_questions,
            difficulty=difficulty,
            context=context,
            bloom_levels=bloom_levels,
        )

        # 调用LLM生成测验
        messages = [
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.4)

        # 确保每道题都有唯一ID
        if "questions" in result:
            for i, q in enumerate(result["questions"]):
                if "id" not in q or not q["id"]:
                    q["id"] = f"q_{uuid.uuid4().hex[:8]}"
                # 确保难度字段正确
                q["difficulty"] = difficulty
                # 确保布鲁姆等级在有效范围内
                if q.get("bloom_level") not in bloom_levels:
                    q["bloom_level"] = min(
                        bloom_levels, key=lambda x: abs(x - q.get("bloom_level", 3))
                    )

        return result

    def generate_quiz_from_document(
        self,
        knowledge_base_id: str,
        topic: str,
        doc_keywords: List[str],
    ) -> dict:
        """
        基于文档关键词生成测验

        Args:
            knowledge_base_id: 知识库ID
            topic: 测验主题
            doc_keywords: 文档关键词列表

        Returns:
            测验字典
        """
        # 使用关键词组合进行更精准的检索
        search_queries = [f"{topic} {kw}" for kw in doc_keywords]

        all_sources = []
        seen_texts = set()
        for query in search_queries:
            sources = rag_engine.get_sources(
                knowledge_base_id=knowledge_base_id,
                question=query,
                k=3,
            )
            for src in sources:
                text = src.get("content", "")
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    all_sources.append(src)

        context = "\n\n".join([src.get("content", "") for src in all_sources])

        # 构建针对文档关键词的提示词
        keywords_str = "、".join(doc_keywords)
        prompt = f"""请根据以下课程内容，围绕关键词「{keywords_str}」生成关于「{topic}」的测验。

要求：
1. 题目必须紧扣给定的关键词，重点考察这些关键概念
2. 生成5道题目，难度覆盖基础到进阶
3. 题型应多样化（选择题、判断题、简答题等）

## 课程内容
{context}

## 输出格式
请严格按照以下JSON格式输出：
```json
{{
  "title": "测验标题（包含关键词提示）",
  "questions": [
    {{
      "id": "q1",
      "type": "multiple_choice",
      "question_text": "题目文本",
      "options": ["选项A", "选项B", "选项C", "选项D"],
      "correct_answer": "选项A",
      "explanation": "详细解析",
      "bloom_level": 1,
      "difficulty": "easy"
    }}
  ]
}}
```

题型说明：multiple_choice（选择题）、true_false（判断题）、short_answer（简答题）、essay（论述题）"""

        messages = [
            {"role": "system", "content": QUIZ_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.4)

        # 确保每道题都有唯一ID
        if "questions" in result:
            for i, q in enumerate(result["questions"]):
                if "id" not in q or not q["id"]:
                    q["id"] = f"q_{uuid.uuid4().hex[:8]}"

        return result

    def evaluate_answer(
        self,
        question: dict,
        user_answer: str,
    ) -> dict:
        """
        评估用户答案

        Args:
            question: 题目字典
            user_answer: 用户的答案

        Returns:
            评估结果字典
        """
        question_type = question.get("type", "short_answer")
        question_text = question.get("question_text", "")
        correct_answer = question.get("correct_answer", "")
        explanation = question.get("explanation", "")
        options = question.get("options", [])

        # 选择题和判断题：精确匹配
        if question_type in ("multiple_choice", "true_false"):
            is_correct = user_answer.strip() == correct_answer.strip()
            score = 100.0 if is_correct else 0.0

            if is_correct:
                feedback = f"回答正确！{explanation}"
            else:
                feedback = (
                    f"回答错误。你选择了「{user_answer}」，正确答案是「{correct_answer}」。\n"
                    f"解析：{explanation}"
                )

            return {
                "score": score,
                "feedback": feedback,
                "correct_answer": correct_answer,
            }

        # 简答题和论述题：使用LLM评估
        prompt = f"""请评估以下问答题的用户答案。

## 题目
{question_text}

{'选项：' + '、'.join(options) if options else ''}

## 正确答案
{correct_answer}

## 解析
{explanation}

## 用户答案
{user_answer}

请按照以下JSON格式输出评估结果：
```json
{{
  "score": 85,
  "feedback": "详细的评估反馈，指出优点和不足",
  "correct_answer": "正确答案的完整表述"
}}
```

评分标准：
- 90-100分：答案完整准确，理解深刻
- 70-89分：答案基本正确，但存在遗漏或小错误
- 50-69分：答案部分正确，存在明显错误或不完整
- 0-49分：答案错误或严重不完整

反馈要求：
1. 先肯定用户回答中正确的部分
2. 指出不足或错误之处
3. 提供改进建议
4. 给出完整的正确答案参考"""

        messages = [
            {"role": "system", "content": "你是一位专业的课程评估教师，请公正、详细地评估学生的答案。"},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.3)

        # 确保 score 是浮点数
        if "score" in result:
            result["score"] = float(result["score"])

        # 确保正确答案字段存在
        if "correct_answer" not in result:
            result["correct_answer"] = correct_answer

        return result
