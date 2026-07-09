"""
知识库管理器模块
负责知识库的创建、管理、文档添加和删除等操作
使用JSON文件存储知识库元数据，MVP阶段不使用数据库
"""

import json
import os
import uuid
import shutil
from datetime import datetime
from typing import List, Optional

from app.core.rag_engine import rag_engine
from app.core.vector_store import vector_store_manager


# 数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data")
KNOWLEDGE_BASES_FILE = os.path.join(DATA_DIR, "knowledge_bases.json")


class KnowledgeBaseManager:
    """知识库管理器，负责知识库的增删查改以及文档管理"""

    def __init__(self):
        """初始化知识库管理器"""
        # 确保数据目录存在
        os.makedirs(DATA_DIR, exist_ok=True)
        # 初始化存储文件
        self._ensure_store_file()

    def _ensure_store_file(self):
        """确保知识库存储文件存在，不存在则创建"""
        if not os.path.exists(KNOWLEDGE_BASES_FILE):
            with open(KNOWLEDGE_BASES_FILE, "w", encoding="utf-8") as f:
                json.dump({"knowledge_bases": {}}, f, ensure_ascii=False, indent=2)

    def _load_store(self) -> dict:
        """从JSON文件加载知识库数据"""
        self._ensure_store_file()
        with open(KNOWLEDGE_BASES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_store(self, data: dict):
        """将知识库数据保存到JSON文件"""
        os.makedirs(os.path.dirname(KNOWLEDGE_BASES_FILE), exist_ok=True)
        with open(KNOWLEDGE_BASES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_kb_data_dir(self, kb_id: str) -> str:
        """获取知识库的数据存储目录"""
        kb_data_dir = os.path.join(DATA_DIR, "kb_files", kb_id)
        os.makedirs(kb_data_dir, exist_ok=True)
        return kb_data_dir

    def create_knowledge_base(self, name: str, description: str, category: str = "general") -> dict:
        """
        创建新的知识库

        参数:
            name: 知识库名称
            description: 知识库描述
            category: 知识库分类

        返回:
            包含知识库信息的字典
        """
        kb_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        kb_metadata = {
            "kb_id": kb_id,
            "name": name,
            "description": description,
            "category": category,
            "created_at": created_at,
            "updated_at": created_at,
            "document_ids": [],
            "status": "active"
        }

        store = self._load_store()
        store["knowledge_bases"][kb_id] = kb_metadata
        self._save_store(store)

        # 创建知识库专属数据目录
        self._get_kb_data_dir(kb_id)

        # 创建对应的向量存储
        try:
            vector_store_manager.create_or_load(kb_id)
        except Exception as e:
            print(f"[警告] 向量存储创建失败: {e}")

        return {
            "kb_id": kb_id,
            "name": name,
            "description": description,
            "category": category,
            "created_at": created_at
        }

    def list_knowledge_bases(self) -> List[dict]:
        """列出所有知识库及其统计信息"""
        store = self._load_store()
        result = []

        for kb_id, kb_data in store["knowledge_bases"].items():
            if kb_data.get("status") == "deleted":
                continue

            stats = self._compute_kb_stats(kb_id, kb_data)

            result.append({
                "kb_id": kb_id,
                "name": kb_data.get("name", ""),
                "description": kb_data.get("description", ""),
                "category": kb_data.get("category", "general"),
                "created_at": kb_data.get("created_at", ""),
                "doc_count": stats["doc_count"],
                "chunk_count": stats["chunk_count"],
                "size_mb": stats["size_mb"]
            })

        result.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return result

    def _compute_kb_stats(self, kb_id: str, kb_data: dict) -> dict:
        """计算知识库的统计数据"""
        doc_count = len(kb_data.get("document_ids", []))
        chunk_count = 0
        size_mb = 0.0

        # 计算文件大小
        kb_data_dir = self._get_kb_data_dir(kb_id)
        if os.path.exists(kb_data_dir):
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(kb_data_dir):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(filepath)
                    except OSError:
                        pass
            size_mb = round(total_size / (1024 * 1024), 2)

        # 从向量存储获取chunk数量
        try:
            chunk_count = vector_store_manager.get_document_count(kb_id)
        except Exception:
            chunk_count = doc_count * 10

        return {
            "doc_count": doc_count,
            "chunk_count": chunk_count,
            "size_mb": size_mb
        }

    def get_knowledge_base(self, kb_id: str) -> dict:
        """获取知识库详情"""
        store = self._load_store()
        kb_data = store["knowledge_bases"].get(kb_id)

        if not kb_data or kb_data.get("status") == "deleted":
            raise ValueError(f"知识库不存在: {kb_id}")

        stats = self._compute_kb_stats(kb_id, kb_data)

        return {
            "kb_id": kb_id,
            "name": kb_data.get("name", ""),
            "description": kb_data.get("description", ""),
            "category": kb_data.get("category", "general"),
            "created_at": kb_data.get("created_at", ""),
            "updated_at": kb_data.get("updated_at", ""),
            "doc_count": stats["doc_count"],
            "chunk_count": stats["chunk_count"],
            "document_ids": kb_data.get("document_ids", []),
            "status": kb_data.get("status", "active")
        }

    def add_documents(self, kb_id: str, file_paths: List[str]) -> dict:
        """
        向知识库添加文档

        使用 rag_engine.ingest_documents 进行文档入库，
        同时将文件复制到知识库数据目录。
        """
        store = self._load_store()
        kb_data = store["knowledge_bases"].get(kb_id)

        if not kb_data or kb_data.get("status") == "deleted":
            raise ValueError(f"知识库不存在: {kb_id}")

        kb_data_dir = self._get_kb_data_dir(kb_id)
        added_documents = []
        failed_documents = []

        # 支持的文件类型
        supported_extensions = {".txt", ".md", ".pdf", ".docx", ".pptx"}

        valid_paths = []
        for file_path in file_paths:
            if not os.path.exists(file_path):
                failed_documents.append({
                    "file_path": file_path,
                    "error": "文件不存在"
                })
                continue

            _, ext = os.path.splitext(file_path)
            if ext.lower() not in supported_extensions:
                failed_documents.append({
                    "file_path": file_path,
                    "error": f"不支持的文件类型: {ext}"
                })
                continue

            try:
                doc_id = str(uuid.uuid4())
                filename = os.path.basename(file_path)
                dest_path = os.path.join(kb_data_dir, f"{doc_id}_{filename}")
                shutil.copy2(file_path, dest_path)
                file_size = os.path.getsize(dest_path)

                doc_info = {
                    "doc_id": doc_id,
                    "filename": filename,
                    "original_path": file_path,
                    "stored_path": dest_path,
                    "size_bytes": file_size,
                    "added_at": datetime.now().isoformat()
                }

                kb_data["document_ids"].append(doc_id)
                if "documents" not in kb_data:
                    kb_data["documents"] = {}
                kb_data["documents"][doc_id] = doc_info
                added_documents.append(doc_info)
                valid_paths.append(dest_path)

            except Exception as e:
                failed_documents.append({
                    "file_path": file_path,
                    "error": str(e)
                })

        # 使用 rag_engine 统一入库
        ingest_result = {"doc_count": 0, "chunk_count": 0}
        if valid_paths:
            try:
                ingest_result = rag_engine.ingest_documents(kb_id, valid_paths)
            except Exception as e:
                print(f"[警告] RAG文档入库失败: {e}")

        # 更新知识库的修改时间
        kb_data["updated_at"] = datetime.now().isoformat()
        store["knowledge_bases"][kb_id] = kb_data
        self._save_store(store)

        return {
            "kb_id": kb_id,
            "added_documents": added_documents,
            "failed_documents": failed_documents,
            "total_added": len(added_documents),
            "total_failed": len(failed_documents),
            "chunk_count": ingest_result.get("chunk_count", 0)
        }

    def delete_knowledge_base(self, kb_id: str) -> bool:
        """删除知识库及其所有数据"""
        store = self._load_store()
        kb_data = store["knowledge_bases"].get(kb_id)

        if not kb_data or kb_data.get("status") == "deleted":
            raise ValueError(f"知识库不存在: {kb_id}")

        # 标记为已删除（软删除）
        kb_data["status"] = "deleted"
        kb_data["deleted_at"] = datetime.now().isoformat()
        store["knowledge_bases"][kb_id] = kb_data
        self._save_store(store)

        # 删除知识库数据目录
        kb_data_dir = self._get_kb_data_dir(kb_id)
        if os.path.exists(kb_data_dir):
            try:
                shutil.rmtree(kb_data_dir)
            except Exception as e:
                print(f"[警告] 删除知识库数据目录失败: {e}")

        # 删除向量存储中的数据
        try:
            vector_store_manager.delete_knowledge_base(kb_id)
        except Exception as e:
            print(f"[警告] 删除向量存储失败: {e}")

        return True

    def get_knowledge_base_stats(self, kb_id: str) -> dict:
        """获取知识库的统计信息"""
        store = self._load_store()
        kb_data = store["knowledge_bases"].get(kb_id)

        if not kb_data or kb_data.get("status") == "deleted":
            raise ValueError(f"知识库不存在: {kb_id}")

        stats = self._compute_kb_stats(kb_id, kb_data)

        return {
            "doc_count": stats["doc_count"],
            "chunk_count": stats["chunk_count"],
            "size_mb": stats["size_mb"],
            "last_updated": kb_data.get("updated_at", kb_data.get("created_at", ""))
        }
