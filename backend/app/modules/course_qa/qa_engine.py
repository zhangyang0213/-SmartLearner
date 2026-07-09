"""
课程问答引擎 - 基于RAG的课程知识问答模块
提供单轮问答、流式问答和多轮对话功能
"""

from typing import List

from app.core.rag_engine import rag_engine


# 课程助教系统提示词
COURSE_QA_SYSTEM_PROMPT = """你是一位耐心、细致的课程教学助手。你的职责是：

1. **深入浅出**：用通俗易懂的语言解释复杂概念，善于使用类比和实例帮助学生理解。
2. **循序渐进**：当学生提出问题时，先确认基础概念是否理解，再逐步深入讲解。
3. **启发引导**：不只是给出答案，更要引导学生思考，帮助他们建立知识之间的联系。
4. **耐心包容**：无论问题多么基础，都要认真对待，绝不对学生的提问表示轻视。
5. **准确严谨**：确保回答内容准确无误，如果不确定，要坦诚说明。
6. **结构清晰**：回答时使用分点、分段等格式，使内容条理清晰，便于理解。
7. **联系实际**：尽可能将理论知识与实际应用场景结合，帮助学生理解知识的价值。

回答时请使用中文，语言风格亲切自然，避免过于机械化。"""


class CourseQAEngine:
    """课程问答引擎，基于RAG技术实现课程知识的智能问答"""

    def ask(self, knowledge_base_id: str, question: str) -> dict:
        """
        单轮问答：根据知识库内容回答课程问题

        Args:
            knowledge_base_id: 知识库ID，指向特定的课程资料库
            question: 学生提出的问题

        Returns:
            包含回答和来源信息的字典
        """
        result = rag_engine.query(
            knowledge_base_id=knowledge_base_id,
            question=question,
        )
        return result

    def ask_stream(self, knowledge_base_id: str, question: str):
        """
        流式问答：逐步返回回答内容，适合实时展示

        Args:
            knowledge_base_id: 知识库ID
            question: 学生提出的问题

        Yields:
            回答文本的增量片段
        """
        yield from rag_engine.streaming_query(
            knowledge_base_id=knowledge_base_id,
            question=question,
        )

    def multi_turn_chat(
        self,
        knowledge_base_id: str,
        question: str,
        history: List[dict],
    ) -> dict:
        """
        多轮对话：在历史对话上下文中进行课程问答

        Args:
            knowledge_base_id: 知识库ID
            question: 当前轮次的学生问题
            history: 历史对话列表

        Returns:
            包含回答和来源信息的字典
        """
        # 验证历史对话格式
        validated_history = []
        for msg in history:
            if msg.get("role") in ("user", "assistant") and msg.get("content"):
                validated_history.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

        # 限制历史对话长度
        max_rounds = 10
        if len(validated_history) > max_rounds * 2:
            validated_history = validated_history[-(max_rounds * 2):]

        # 构建包含历史上下文的问题
        context_parts = []
        for msg in validated_history[-6:]:  # 只取最近3轮对话避免过长
            role = "用户" if msg["role"] == "user" else "助手"
            context_parts.append(f"{role}: {msg['content']}")

        context_str = "\n".join(context_parts)
        enhanced_question = f"{context_str}\n\n用户最新问题: {question}"

        result = rag_engine.query(
            knowledge_base_id=knowledge_base_id,
            question=enhanced_question,
        )

        return result
