"""
向量存储管理模块
使用 FAISS 进行向量索引的创建、加载、检索和删除
"""

import os
import shutil
import logging
from typing import List

from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS

from app.config import settings
from app.core.embedding import get_embeddings

logger = logging.getLogger(__name__)


class VectorStoreManager:
    """
    向量存储管理器
    管理多个知识库的 FAISS 索引，支持创建、加载、检索和删除操作

    每个知识库对应一个独立的 FAISS 索引，
    存储路径为 {VECTOR_STORE_PATH}/{knowledge_base_id}/
    """

    def __init__(self) -> None:
        """初始化向量存储管理器"""
        self._store_path = settings.VECTOR_STORE_PATH
        self._embeddings = get_embeddings()
        # 缓存已加载的 FAISS 索引，避免重复从磁盘加载
        self._cache: dict[str, FAISS] = {}
        os.makedirs(self._store_path, exist_ok=True)

    def _get_kb_path(self, knowledge_base_id: str) -> str:
        """
        获取知识库的存储路径

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            知识库的 FAISS 索引存储路径
        """
        return os.path.join(self._store_path, knowledge_base_id)

    def create_or_load(self, knowledge_base_id: str) -> FAISS:
        """
        创建或加载知识库的 FAISS 索引

        如果知识库已存在于磁盘，则从磁盘加载；
        如果缓存中已有，则直接返回缓存实例；
        否则创建空的 FAISS 索引。

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            FAISS 向量存储实例
        """
        # 优先从缓存获取
        if knowledge_base_id in self._cache:
            logger.info(f"从缓存加载知识库向量索引: {knowledge_base_id}")
            return self._cache[knowledge_base_id]

        kb_path = self._get_kb_path(knowledge_base_id)

        # 尝试从磁盘加载已有索引
        if os.path.exists(kb_path) and os.listdir(kb_path):
            try:
                vectorstore = FAISS.load_local(
                    kb_path,
                    self._embeddings,
                    allow_dangerous_deserialization=True,
                )
                self._cache[knowledge_base_id] = vectorstore
                logger.info(f"从磁盘加载知识库向量索引: {knowledge_base_id}")
                return vectorstore
            except Exception as e:
                logger.warning(
                    f"加载知识库 {knowledge_base_id} 的向量索引失败: {e}，将创建新索引"
                )

        # 创建空的 FAISS 索引
        # 使用一个临时文档来初始化 FAISS，然后删除它
        dummy_doc = Document(
            page_content="__init__",
            metadata={"source": "__init__", "page": 0, "file_type": "init"},
        )
        vectorstore = FAISS.from_documents([dummy_doc], self._embeddings)
        # 删除初始化用的临时文档
        all_ids = vectorstore.index_to_docstore_id.values()
        vectorstore.delete(list(all_ids))

        self._cache[knowledge_base_id] = vectorstore
        logger.info(f"创建新知识库向量索引: {knowledge_base_id}")
        return vectorstore

    def _save(self, knowledge_base_id: str, vectorstore: FAISS) -> None:
        """
        将 FAISS 索引保存到磁盘

        Args:
            knowledge_base_id: 知识库ID
            vectorstore: FAISS 向量存储实例
        """
        kb_path = self._get_kb_path(knowledge_base_id)
        os.makedirs(kb_path, exist_ok=True)
        vectorstore.save_local(kb_path)
        logger.info(f"保存知识库向量索引: {knowledge_base_id}")

    def add_documents(
        self, knowledge_base_id: str, documents: List[Document]
    ) -> None:
        """
        向知识库添加文档

        如果知识库已存在，则追加文档；否则先创建新的索引。

        Args:
            knowledge_base_id: 知识库ID
            documents: 要添加的 Document 列表
        """
        if not documents:
            logger.warning(f"知识库 {knowledge_base_id} 没有文档可添加")
            return

        vectorstore = self.create_or_load(knowledge_base_id)
        vectorstore.add_documents(documents)
        self._save(knowledge_base_id, vectorstore)
        logger.info(
            f"向知识库 {knowledge_base_id} 添加了 {len(documents)} 个文档分块"
        )

    def similarity_search(
        self, knowledge_base_id: str, query: str, k: int = 5
    ) -> List[Document]:
        """
        在知识库中进行相似性搜索

        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            k: 返回最相似的文档数量

        Returns:
            最相似的 k 个 Document 列表
        """
        vectorstore = self.create_or_load(knowledge_base_id)
        results = vectorstore.similarity_search(query, k=k)
        logger.info(
            f"知识库 {knowledge_base_id} 相似性搜索返回 {len(results)} 个结果"
        )
        return results

    def similarity_search_with_score(
        self, knowledge_base_id: str, query: str, k: int = 5
    ) -> List[tuple[Document, float]]:
        """
        在知识库中进行相似性搜索并返回分数

        Args:
            knowledge_base_id: 知识库ID
            query: 查询文本
            k: 返回最相似的文档数量

        Returns:
            最相似的 k 个 (Document, score) 元组列表，score 为 L2 距离
        """
        vectorstore = self.create_or_load(knowledge_base_id)
        results = vectorstore.similarity_search_with_score(query, k=k)
        logger.info(
            f"知识库 {knowledge_base_id} 相似性搜索（含分数）返回 {len(results)} 个结果"
        )
        return results

    def delete_knowledge_base(self, knowledge_base_id: str) -> None:
        """
        删除知识库及其向量索引

        同时清除缓存和磁盘上的索引文件。

        Args:
            knowledge_base_id: 知识库ID
        """
        # 清除缓存
        if knowledge_base_id in self._cache:
            del self._cache[knowledge_base_id]

        # 删除磁盘文件
        kb_path = self._get_kb_path(knowledge_base_id)
        if os.path.exists(kb_path):
            shutil.rmtree(kb_path)
            logger.info(f"删除知识库向量索引: {knowledge_base_id}")
        else:
            logger.warning(f"知识库 {knowledge_base_id} 的向量索引不存在于磁盘")

    def get_document_count(self, knowledge_base_id: str) -> int:
        """
        获取知识库中的文档数量

        Args:
            knowledge_base_id: 知识库ID

        Returns:
            知识库中向量（文档分块）的数量
        """
        vectorstore = self.create_or_load(knowledge_base_id)
        return vectorstore.index.ntotal


# 全局单例
vector_store_manager = VectorStoreManager()
