"""
核心 RAG 引擎模块
实现检索增强生成（Retrieval-Augmented Generation）的完整流程
包括文档入库、查询检索、答案生成和流式输出
"""

import logging
from typing import List, Generator

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.core.llm import get_llm, get_fast_llm
from app.core.document_parser import parse_document, chunk_documents
from app.core.vector_store import vector_store_manager

logger = logging.getLogger(__name__)

# RAG 系统提示模板
RAG_PROMPT_TEMPLATE = """你是一个智能学习助手。基于以下参考资料回答问题。

参考资料：
{context}

问题：{question}

请基于参考资料给出详细回答，如果资料中没有相关信息，请说明。"""


class RAGEngine:
    """
    RAG 引擎类
    整合文档解析、向量检索和 LLM 生成，提供完整的 RAG 问答能力
    """

    def __init__(self) -> None:
        """初始化 RAG 引擎"""
        self._vector_store = vector_store_manager

    def ingest_documents(
        self, knowledge_base_id: str, file_paths: List[str]
    ) -> dict:
        """
        将文档导入知识库

        解析文件、分块、生成向量嵌入并存入 FAISS 索引。

        Args:
            knowledge_base_id: 知识库ID
            file_paths: 文件路径列表

        Returns:
            包含 doc_count（文档数）和 chunk_count（分块数）的字典
        """
        all_chunks: List[Document] = []
        doc_count = 0

        for file_path in file_paths:
            try:
                logger.info(f"开始处理文档: {file_path}")
                # 解析文档
                documents = parse_document(file_path)
                # 分块
                chunks = chunk_documents(documents)
                all_chunks.extend(chunks)
                doc_count += 1
                logger.info(
                    f"文档 {file_path} 处理完成："
                    f"原始 {len(documents)} 段 -> {len(chunks)} 个分块"
                )
            except Exception as e:
                logger.error(f"处理文档 {file_path} 失败: {e}")
                # 继续处理其他文件，不中断整个流程
                continue

        if all_chunks:
            self._vector_store.add_documents(knowledge_base_id, all_chunks)
            logger.info(
                f"知识库 {knowledge_base_id} 文档导入完成："
                f"{doc_count} 个文档，{len(all_chunks)} 个分块"
            )
        else:
            logger.warning(
                f"知识库 {knowledge_base_id} 没有成功导入任何文档分块"
            )

        return {
            "doc_count": doc_count,
            "chunk_count": len(all_chunks),
        }

    def query(
        self, knowledge_base_id: str, question: str, k: int = 5
    ) -> dict:
        """
        基于知识库进行 RAG 查询

        检索相关文档、构造提示词、调用 LLM 生成回答。

        Args:
            knowledge_base_id: 知识库ID
            question: 用户问题
            k: 检索的文档数量

        Returns:
            包含 answer（答案）、sources（来源）和 confidence（置信度）的字典
        """
        # 1. 检索相关文档（带分数）
        search_results = self._vector_store.similarity_search_with_score(
            knowledge_base_id, question, k=k
        )

        if not search_results:
            return {
                "answer": "知识库中没有找到相关的参考资料，无法回答您的问题。",
                "sources": [],
                "confidence": 0.0,
            }

        # 2. 分离文档和分数
        documents, scores = zip(*search_results)

        # 3. 构建上下文文本
        context_parts = []
        sources = []
        for i, (doc, score) in enumerate(zip(documents, scores), start=1):
            source_info = {
                "content": doc.page_content[:200] + "..."
                if len(doc.page_content) > 200
                else doc.page_content,
                "source": doc.metadata.get("source", "未知"),
                "page": doc.metadata.get("page", 0),
                "file_type": doc.metadata.get("file_type", "未知"),
                "score": float(score),
            }
            sources.append(source_info)
            context_parts.append(f"[参考资料 {i}]\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        # 4. 构建提示并调用 LLM
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        llm = get_llm(temperature=0.7)
        chain = prompt | llm | StrOutputParser()

        answer = chain.invoke({"context": context, "question": question})

        # 5. 计算置信度（基于最相似文档的分数）
        # FAISS L2 距离越小越相似，转换为 0-1 置信度
        best_score = float(min(scores))
        confidence = float(max(0.0, min(1.0, 1.0 / (1.0 + best_score))))

        logger.info(
            f"知识库 {knowledge_base_id} RAG 查询完成："
            f"检索 {len(documents)} 个文档，置信度 {confidence:.2f}"
        )

        return {
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 4),
        }

    def streaming_query(
        self, knowledge_base_id: str, question: str, k: int = 5
    ) -> Generator[str, None, None]:
        """
        基于知识库进行流式 RAG 查询

        逐 token 生成回答，适合实时展示的场景。

        Args:
            knowledge_base_id: 知识库ID
            question: 用户问题
            k: 检索的文档数量

        Yields:
            生成的文本 token
        """
        # 1. 检索相关文档
        documents = self._vector_store.similarity_search(
            knowledge_base_id, question, k=k
        )

        if not documents:
            yield "知识库中没有找到相关的参考资料，无法回答您的问题。"
            return

        # 2. 构建上下文文本
        context_parts = []
        for i, doc in enumerate(documents, start=1):
            context_parts.append(f"[参考资料 {i}]\n{doc.page_content}")

        context = "\n\n".join(context_parts)

        # 3. 构建流式 LLM 调用
        prompt = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)
        llm = get_llm(temperature=0.7, streaming=True)
        chain = prompt | llm | StrOutputParser()

        # 4. 流式输出
        for token in chain.stream({"context": context, "question": question}):
            yield token

    def get_sources(
        self, knowledge_base_id: str, question: str, k: int = 5
    ) -> List[dict]:
        """
        仅检索相关文档来源，不生成回答

        适用于只需要查看相关参考资料的场景。

        Args:
            knowledge_base_id: 知识库ID
            question: 用户问题
            k: 检索的文档数量

        Returns:
            来源信息字典列表
        """
        search_results = self._vector_store.similarity_search_with_score(
            knowledge_base_id, question, k=k
        )

        sources = []
        for doc, score in search_results:
            sources.append(
                {
                    "content": doc.page_content[:300] + "..."
                    if len(doc.page_content) > 300
                    else doc.page_content,
                    "source": doc.metadata.get("source", "未知"),
                    "page": doc.metadata.get("page", 0),
                    "file_type": doc.metadata.get("file_type", "未知"),
                    "score": float(score),
                }
            )
        return sources


# 全局单例
rag_engine = RAGEngine()


def get_rag_engine() -> RAGEngine:
    """获取全局 RAG 引擎单例"""
    return rag_engine
