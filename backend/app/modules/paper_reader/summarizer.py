"""
论文摘要生成器 - 对学术论文进行结构化摘要与关键信息提取
支持全文摘要、快速摘要、关键概念提取和方法论提取
"""

from typing import List

from app.core.rag_engine import rag_engine
from app.core.llm import LLMClient


# 论文摘要系统提示词
PAPER_SUMMARY_SYSTEM_PROMPT = """你是一位资深的学术研究分析专家，擅长阅读和分析学术论文。你的任务是对论文进行深入、准确的结构化分析。

你的分析原则：
1. **准确性**：严格基于论文内容，不添加论文中没有的信息
2. **结构化**：按照学术规范组织分析结果，逻辑清晰
3. **深度**：不仅描述表面内容，更要挖掘研究背后的逻辑和贡献
4. **简洁**：用精炼的语言概括核心观点，避免冗余
5. **批判性**：客观评价论文的优缺点和局限性
6. 所有输出使用中文"""


class PaperSummarizer:
    """论文摘要生成器，基于RAG检索论文内容并生成结构化摘要"""

    def __init__(self):
        """初始化论文摘要生成器"""
        self.llm = LLMClient()

    def _retrieve_paper_content(
        self, knowledge_base_id: str, query: str = "", k: int = 15
    ) -> str:
        """从知识库中检索论文内容并拼接为上下文"""
        queries = [query] if query else []
        default_queries = [
            "论文摘要 研究目的 研究方法",
            "实验结果 结论 贡献",
            "研究背景 相关工作 局限性",
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

    def summarize(self, knowledge_base_id: str) -> dict:
        """
        生成论文全文摘要

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            结构化摘要字典
        """
        context = self._retrieve_paper_content(knowledge_base_id)

        prompt = f"""请对以下论文内容进行全面的结构化分析，提取关键信息并生成摘要。

## 论文内容
{context}

## 输出格式
请严格按照以下JSON格式输出，不要添加任何其他内容：
```json
{{
  "title_guess": "推测的论文标题（从内容中推断）",
  "abstract_summary": "对论文摘要的精炼总结（200-300字），涵盖研究问题、方法和主要结论",
  "key_contributions": [
    "贡献1：具体描述第一个主要贡献",
    "贡献2：具体描述第二个主要贡献",
    "贡献3：具体描述第三个主要贡献"
  ],
  "methodology_summary": "研究方法的详细总结（200-300字）",
  "findings_summary": "研究发现的详细总结（200-300字）",
  "limitations": "论文的局限性分析",
  "future_work": "基于论文内容推测的未来研究方向",
  "overall_assessment": "对论文的总体评价（150-200字）"
}}
```

注意：
- key_contributions 列表至少包含2项，不超过5项
- 所有内容必须基于论文原文，不要编造
- 评价要客观公正，既指出亮点也指出不足"""

        messages = [
            {"role": "system", "content": PAPER_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.3)

        # 确保必要字段存在
        default_result = {
            "title_guess": "",
            "abstract_summary": "",
            "key_contributions": [],
            "methodology_summary": "",
            "findings_summary": "",
            "limitations": [],
            "future_work": "",
            "overall_assessment": "",
        }
        for key in default_result:
            if key not in result:
                result[key] = default_result[key]

        # 确保 limitations 和 key_contributions 是列表
        if isinstance(result.get("limitations"), str):
            text = result["limitations"].strip()
            result["limitations"] = [text] if text else []
        if isinstance(result.get("key_contributions"), str):
            text = result["key_contributions"].strip()
            result["key_contributions"] = [text] if text else []

        return result

    def quick_summary(self, knowledge_base_id: str) -> str:
        """
        生成快速摘要：用3句话概括论文的核心内容

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            3句话的快速摘要文本
        """
        context = self._retrieve_paper_content(knowledge_base_id, k=8)

        prompt = f"""请用恰好3句话概括以下论文的核心内容。

要求：
- 第1句话：论文研究了什么问题
- 第2句话：用了什么方法
- 第3句话：得出了什么结论

## 论文内容
{context}

请直接输出3句话的摘要，不需要任何额外格式或标记。"""

        messages = [
            {"role": "system", "content": PAPER_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat(messages=messages, temperature=0.3)
        return result.strip()

    def extract_key_concepts(self, knowledge_base_id: str) -> List[dict]:
        """
        提取关键概念

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            关键概念列表
        """
        concept_queries = [
            "定义 概念 术语 理论框架",
            "核心方法 算法 模型 关键技术",
            "假设 变量 参数 公式",
        ]

        all_contents = []
        seen_texts = set()

        for query in concept_queries:
            sources = rag_engine.get_sources(
                knowledge_base_id=knowledge_base_id,
                question=query,
                k=8,
            )
            for src in sources:
                text = src.get("content", "")
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    all_contents.append(text)

        context = "\n\n".join(all_contents)

        prompt = f"""请从以下论文内容中提取关键概念和术语。

## 论文内容
{context}

## 输出格式
请严格按照以下JSON格式输出：
```json
{{
  "key_concepts": [
    {{
      "concept": "概念名称",
      "definition": "该概念在论文中的定义或解释",
      "context": "该概念在论文研究中的具体应用和上下文",
      "related_concepts": ["相关概念1", "相关概念2"]
    }}
  ]
}}
```

提取5-10个最重要的概念。"""

        messages = [
            {"role": "system", "content": PAPER_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.3)

        concepts = result.get("key_concepts", [])
        if not concepts and isinstance(result, list):
            concepts = result

        return concepts

    def extract_methodology(self, knowledge_base_id: str) -> dict:
        """
        提取研究方法论

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            方法论详情字典
        """
        method_queries = [
            "研究方法 实验设计 数据集 基线",
            "评估指标 评价指标 对比实验 消融实验",
            "算法流程 模型架构 训练策略 参数设置",
        ]

        all_contents = []
        seen_texts = set()

        for query in method_queries:
            sources = rag_engine.get_sources(
                knowledge_base_id=knowledge_base_id,
                question=query,
                k=8,
            )
            for src in sources:
                text = src.get("content", "")
                if text and text not in seen_texts:
                    seen_texts.add(text)
                    all_contents.append(text)

        context = "\n\n".join(all_contents)

        prompt = f"""请从以下论文内容中提取详细的研究方法论信息。

## 论文内容
{context}

## 输出格式
请严格按照以下JSON格式输出：
```json
{{
  "research_type": "研究类型",
  "research_questions": ["研究问题1", "研究问题2"],
  "data_sources": ["数据来源1", "数据来源2"],
  "methods_used": [
    {{
      "name": "方法名称",
      "description": "方法描述",
      "purpose": "该方法用于解决什么问题"
    }}
  ],
  "experimental_design": "实验设计描述",
  "evaluation_metrics": ["评估指标1", "评估指标2"],
  "baseline_comparisons": ["基线方法1", "基线方法2"],
  "statistical_methods": ["统计方法1"]
}}
```"""

        messages = [
            {"role": "system", "content": PAPER_SUMMARY_SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        result = self.llm.chat_json(messages=messages, temperature=0.3)

        default_result = {
            "research_type": "",
            "research_questions": [],
            "data_sources": [],
            "methods_used": [],
            "experimental_design": "",
            "evaluation_metrics": [],
            "baseline_comparisons": [],
            "statistical_methods": [],
        }
        for key in default_result:
            if key not in result:
                result[key] = default_result[key]

        return result
