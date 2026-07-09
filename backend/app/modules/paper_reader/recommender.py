"""
文献推荐引擎 - 基于论文内容的智能文献推荐与知识图谱构建
支持相关文献推荐、文献图谱生成和反面观点发现
"""

from typing import List

from app.core.rag_engine import rag_engine
from app.core.llm import LLMClient


# 文献推荐系统提示词
LITERATURE_RECOMMENDER_SYSTEM_PROMPT = """你是一位博学的学术文献顾问，擅长根据论文内容推荐相关的学术资源。你的推荐要遵循以下原则：

1. **相关性**：推荐内容必须与论文主题紧密相关
2. **层次性**：推荐应覆盖从基础到前沿的不同层次
3. **多元性**：推荐应包括不同观点和方法论的研究
4. **实用性**：给出具体的搜索建议
5. **批判性**：不仅要推荐支持性文献，也要推荐挑战性观点
6. 所有输出使用中文"""


class LiteratureRecommender:
    """文献推荐引擎，基于论文内容进行智能文献推荐和知识图谱构建"""

    def __init__(self):
        """初始化文献推荐引擎"""
        self.llm = LLMClient()

    def _retrieve_paper_content(
        self, knowledge_base_id: str, query: str = "", k: int = 10
    ) -> str:
        """从知识库中检索论文内容"""
        queries = [query] if query else []
        default_queries = [
            "论文标题 摘要 关键词 研究领域",
            "核心方法 理论框架 主要贡献",
            "相关工作 文献综述 引用 参考文献",
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

    def recommend_related(
        self,
        knowledge_base_id: str,
        num_results: int = 5,
    ) -> List[dict]:
        """
        推荐相关文献

        Args:
            knowledge_base_id: 知识库ID
            num_results: 推荐结果数量

        Returns:
            推荐文献列表
        """
        context = self._retrieve_paper_content(knowledge_base_id)

        prompt = f"""请根据以下论文内容，推荐相关的学术文献。

## 论文内容
{context}

请严格按照以下JSON格式输出：
```json
{{
  "recommendations": [
    {{
      "title": "推荐文献的推测标题",
      "authors_guess": "可能的相关作者或研究团队",
      "relevance_reason": "与当前论文的相关性说明",
      "search_query": "搜索查询词",
      "topics_shared": ["共享的主题1", "共享的主题2"]
    }}
  ]
}}
```

推荐 {num_results} 篇相关文献。"""

        messages = [
            {"role": "system", "content": LITERATURE_RECOMMENDER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.5)

        recommendations = result.get("recommendations", [])
        if not recommendations and isinstance(result, list):
            recommendations = result

        for rec in recommendations:
            rec.setdefault("title", "")
            rec.setdefault("authors_guess", "")
            rec.setdefault("relevance_reason", "")
            rec.setdefault("search_query", "")
            rec.setdefault("topics_shared", [])

        return recommendations[:num_results]

    def generate_literature_map(self, knowledge_base_id: str) -> dict:
        """
        生成文献图谱

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            文献图谱字典
        """
        context = self._retrieve_paper_content(knowledge_base_id)

        prompt = f"""请根据以下论文内容，构建一个文献知识图谱。

## 论文内容
{context}

请严格按照以下JSON格式输出：
```json
{{
  "core_topics": ["核心主题1", "核心主题2"],
  "related_fields": ["相关领域1", "相关领域2"],
  "suggested_readings": {{
    "foundational": [
      {{
        "title": "基础文献标题",
        "authors_guess": "作者",
        "relevance_reason": "为什么是基础",
        "search_query": "搜索查询词"
      }}
    ],
    "advanced": [
      {{
        "title": "进阶文献标题",
        "authors_guess": "作者",
        "relevance_reason": "为什么是进阶",
        "search_query": "搜索查询词"
      }}
    ],
    "interdisciplinary": [
      {{
        "title": "跨学科文献标题",
        "authors_guess": "作者",
        "relevance_reason": "为什么跨学科",
        "search_query": "搜索查询词"
      }}
    ]
  }}
}}
```"""

        messages = [
            {"role": "system", "content": LITERATURE_RECOMMENDER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.5)

        if "core_topics" not in result:
            result["core_topics"] = []
        if "related_fields" not in result:
            result["related_fields"] = []
        if "suggested_readings" not in result:
            result["suggested_readings"] = {}

        for reading_type in ("foundational", "advanced", "interdisciplinary"):
            if reading_type not in result["suggested_readings"]:
                result["suggested_readings"][reading_type] = []
            for item in result["suggested_readings"][reading_type]:
                for field in ("title", "authors_guess", "relevance_reason", "search_query"):
                    if field not in item:
                        item[field] = ""

        return result

    def find_contradicting_views(self, knowledge_base_id: str) -> List[dict]:
        """
        发现反面观点

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            反面观点列表
        """
        context = self._retrieve_paper_content(
            knowledge_base_id, query="结论 贡献 论证 假设 局限"
        )

        prompt = f"""请分析以下论文内容，找出可能挑战或反驳该论文结论的观点。

## 论文内容
{context}

请严格按照以下JSON格式输出：
```json
{{
  "contradicting_views": [
    {{
      "potential_counter_argument": "潜在的反驳论点",
      "search_direction": "搜索方向和建议",
      "key_questions_to_explore": ["关键问题1", "关键问题2"]
    }}
  ]
}}
```

提出3-5个潜在的反面观点。"""

        messages = [
            {"role": "system", "content": LITERATURE_RECOMMENDER_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.6)

        contradicting_views = result.get("contradicting_views", [])
        if not contradicting_views and isinstance(result, list):
            contradicting_views = result

        for view in contradicting_views:
            view.setdefault("potential_counter_argument", "")
            view.setdefault("search_direction", "")
            view.setdefault("key_questions_to_explore", [])

        return contradicting_views
