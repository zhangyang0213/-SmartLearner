"""
混合搜索引擎模块
支持语义搜索、关键词搜索（TF-IDF）和混合搜索
使用LLM进行查询优化和结果重排序
"""

import json
import math
import os
import re
import logging
from collections import Counter, defaultdict
from typing import List, Optional

from app.core.vector_store import vector_store_manager
from app.core.embedding import get_embeddings
from app.core.llm import LLMClient

logger = logging.getLogger(__name__)

# 数据存储路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data")
KNOWLEDGE_BASES_FILE = os.path.join(DATA_DIR, "knowledge_bases.json")


class TFIDFEngine:
    """
    基于TF-IDF的关键词搜索引擎
    实现简单的BM25风格检索，不依赖外部库
    """

    def __init__(self):
        """初始化TF-IDF引擎"""
        self.documents = {}
        self.inverted_index = defaultdict(dict)
        self.doc_count = 0
        self.avg_doc_length = 0
        self.k1 = 1.5
        self.b = 0.75

    def _tokenize(self, text: str) -> List[str]:
        """对文本进行分词处理"""
        text = text.lower()
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text)
        english_words = re.findall(r'[a-z]+[a-z0-9]*', text)
        numbers = re.findall(r'\d+', text)

        bigrams = []
        for word in english_words:
            if len(word) >= 4:
                for i in range(len(word) - 1):
                    bigrams.append(word[i:i+2])

        return chinese_chars + english_words + numbers + bigrams

    def add_document(self, doc_id: str, content: str, metadata: dict = None):
        """添加文档到索引"""
        terms = self._tokenize(content)
        term_freq = Counter(terms)

        self.documents[doc_id] = {
            "content": content,
            "metadata": metadata or {},
            "terms": term_freq,
            "length": len(terms)
        }

        for term, freq in term_freq.items():
            self.inverted_index[term][doc_id] = freq

        self.doc_count = len(self.documents)
        total_length = sum(doc["length"] for doc in self.documents.values())
        self.avg_doc_length = total_length / self.doc_count if self.doc_count > 0 else 0

    def remove_document(self, doc_id: str):
        """从索引中移除文档"""
        if doc_id not in self.documents:
            return

        doc = self.documents[doc_id]
        for term in doc["terms"]:
            if term in self.inverted_index and doc_id in self.inverted_index[term]:
                del self.inverted_index[term][doc_id]
                if not self.inverted_index[term]:
                    del self.inverted_index[term]

        del self.documents[doc_id]
        self.doc_count = len(self.documents)
        if self.doc_count > 0:
            total_length = sum(doc["length"] for doc in self.documents.values())
            self.avg_doc_length = total_length / self.doc_count
        else:
            self.avg_doc_length = 0

    def search(self, query: str, k: int = 5) -> List[dict]:
        """使用BM25算法搜索文档"""
        if not self.documents:
            return []

        query_terms = self._tokenize(query)
        scores = defaultdict(float)

        for term in query_terms:
            if term not in self.inverted_index:
                continue

            df = len(self.inverted_index[term])
            idf = math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1)

            for doc_id, tf in self.inverted_index[term].items():
                doc = self.documents[doc_id]
                tf_norm = (tf * (self.k1 + 1)) / (
                    tf + self.k1 * (1 - self.b + self.b * doc["length"] / self.avg_doc_length)
                )
                scores[doc_id] += idf * tf_norm

        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:k]

        results = []
        for doc_id, score in sorted_results:
            doc = self.documents[doc_id]
            results.append({
                "content": doc["content"],
                "metadata": doc["metadata"],
                "score": float(score),
                "source": doc["metadata"].get("filename", doc_id)
            })

        return results

    def clear(self):
        """清空所有索引数据"""
        self.documents.clear()
        self.inverted_index.clear()
        self.doc_count = 0
        self.avg_doc_length = 0


class HybridSearchEngine:
    """
    混合搜索引擎
    支持语义搜索、关键词搜索和混合搜索三种模式
    """

    def __init__(self):
        """初始化混合搜索引擎"""
        self.llm = LLMClient()
        self.tfidf_engines = {}
        self._max_cached_engines = 50

    def _get_tfidf_engine(self, kb_id: str) -> TFIDFEngine:
        """获取或创建指定知识库的TF-IDF引擎"""
        if kb_id not in self.tfidf_engines:
            engine = TFIDFEngine()
            self._load_kb_documents(kb_id, engine)
            self.tfidf_engines[kb_id] = engine

            if len(self.tfidf_engines) > self._max_cached_engines:
                oldest_key = next(iter(self.tfidf_engines))
                del self.tfidf_engines[oldest_key]

        return self.tfidf_engines[kb_id]

    def _load_kb_documents(self, kb_id: str, engine: TFIDFEngine):
        """从知识库加载文档到TF-IDF引擎"""
        # 从向量存储加载文档内容（使用similarity_search获取全部文档）
        try:
            doc_count = vector_store_manager.get_document_count(kb_id)
            if doc_count > 0:
                # 使用一个宽泛查询获取所有文档
                docs = vector_store_manager.similarity_search(
                    kb_id, "知识库内容", k=min(doc_count, 100)
                )
                for i, doc in enumerate(docs):
                    doc_id = f"doc_{i}"
                    content = doc.page_content
                    metadata = doc.metadata
                    if content:
                        engine.add_document(doc_id, content, metadata)
                return
        except Exception as e:
            logger.warning(f"从向量存储加载文档失败: {e}")

        # 回退：从知识库JSON文件加载
        if os.path.exists(KNOWLEDGE_BASES_FILE):
            try:
                with open(KNOWLEDGE_BASES_FILE, "r", encoding="utf-8") as f:
                    store = json.load(f)
                kb_data = store.get("knowledge_bases", {}).get(kb_id, {})
                documents = kb_data.get("documents", {})
                kb_data_dir = os.path.join(DATA_DIR, "kb_files", kb_id)

                for doc_id, doc_info in documents.items():
                    stored_path = doc_info.get("stored_path", "")
                    if stored_path and os.path.exists(stored_path):
                        try:
                            with open(stored_path, "r", encoding="utf-8") as f:
                                content = f.read()
                            engine.add_document(doc_id, content, doc_info)
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"从JSON文件加载文档失败: {e}")

    def _semantic_search(self, kb_id: str, query: str, k: int = 5) -> List[dict]:
        """语义搜索：使用向量相似度搜索"""
        try:
            results = vector_store_manager.similarity_search_with_score(
                kb_id, query, k=k
            )
            formatted_results = []
            for doc, score in results:
                formatted_results.append({
                    "content": doc.page_content,
                    "metadata": doc.metadata,
                    "score": float(score),
                    "source": doc.metadata.get("source", "")
                })
            return formatted_results
        except Exception as e:
            logger.error(f"语义搜索失败: {e}")
            return []

    def _keyword_search(self, kb_id: str, query: str, k: int = 5) -> List[dict]:
        """关键词搜索：使用BM25/TF-IDF搜索"""
        engine = self._get_tfidf_engine(kb_id)
        if engine.doc_count == 0:
            return []
        return engine.search(query, k=k)

    def _normalize_scores(self, results: List[dict]) -> List[dict]:
        """将搜索结果的分数归一化到[0, 1]区间"""
        if not results:
            return results

        scores = [r["score"] for r in results]
        min_score = min(scores)
        max_score = max(scores)
        score_range = max_score - min_score

        for result in results:
            if score_range > 0:
                result["score"] = (result["score"] - min_score) / score_range
            else:
                result["score"] = 1.0

        return results

    def search(self, kb_id: str, query: str, k: int = 5, search_type: str = "hybrid") -> List[dict]:
        """
        搜索知识库

        参数:
            kb_id: 知识库ID
            query: 查询文本
            k: 返回结果数量
            search_type: 搜索类型 semantic/keyword/hybrid

        返回:
            搜索结果列表
        """
        if search_type == "semantic":
            results = self._semantic_search(kb_id, query, k=k)
            return results[:k]

        elif search_type == "keyword":
            results = self._keyword_search(kb_id, query, k=k)
            return results[:k]

        elif search_type == "hybrid":
            semantic_weight = 0.7
            keyword_weight = 0.3

            fetch_k = k * 3
            semantic_results = self._semantic_search(kb_id, query, k=fetch_k)
            keyword_results = self._keyword_search(kb_id, query, k=fetch_k)

            semantic_results = self._normalize_scores(semantic_results)
            keyword_results = self._normalize_scores(keyword_results)

            merged = {}

            for result in semantic_results:
                content_key = result["content"][:100]
                merged[content_key] = {
                    "content": result["content"],
                    "metadata": result["metadata"],
                    "semantic_score": result["score"],
                    "keyword_score": 0.0,
                    "source": result["source"]
                }

            for result in keyword_results:
                content_key = result["content"][:100]
                if content_key in merged:
                    merged[content_key]["keyword_score"] = result["score"]
                else:
                    merged[content_key] = {
                        "content": result["content"],
                        "metadata": result["metadata"],
                        "semantic_score": 0.0,
                        "keyword_score": result["score"],
                        "source": result["source"]
                    }

            final_results = []
            for item in merged.values():
                combined_score = (
                    semantic_weight * item["semantic_score"] +
                    keyword_weight * item["keyword_score"]
                )
                final_results.append({
                    "content": item["content"],
                    "metadata": item["metadata"],
                    "score": round(combined_score, 4),
                    "source": item["source"]
                })

            final_results.sort(key=lambda x: x["score"], reverse=True)
            return final_results[:k]

        else:
            raise ValueError(f"不支持的搜索类型: {search_type}，请使用 'semantic'、'keyword' 或 'hybrid'")

    def multi_kb_search(self, kb_ids: List[str], query: str, k: int = 5) -> List[dict]:
        """跨多个知识库搜索"""
        all_results = []

        for kb_id in kb_ids:
            try:
                results = self.search(kb_id, query, k=k, search_type="hybrid")
                for result in results:
                    result["metadata"]["kb_id"] = kb_id
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"知识库 {kb_id} 搜索失败: {e}")
                continue

        seen = set()
        unique_results = []
        for result in all_results:
            content_key = result["content"][:100]
            if content_key not in seen:
                seen.add(content_key)
                unique_results.append(result)

        unique_results.sort(key=lambda x: x["score"], reverse=True)
        return unique_results[:k]

    def natural_language_query(self, kb_id: str, query: str) -> dict:
        """
        自然语言查询：使用LLM优化搜索查询，然后执行搜索并生成摘要
        """
        # 第一步：使用LLM优化查询
        refined_query = query
        try:
            refine_messages = [
                {"role": "system", "content": "你是一个搜索查询优化专家。将用户查询优化为更有效的搜索关键词。只输出优化后的查询，不要添加额外解释。"},
                {"role": "user", "content": f"用户查询：{query}\n\n请提取核心概念和关键词，添加相关同义词。优化后的搜索查询："},
            ]
            refined_query = self.llm.chat(messages=refine_messages, temperature=0.3)
            refined_query = refined_query.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning(f"LLM优化查询失败，使用原始查询: {e}")
            refined_query = query

        # 第二步：执行搜索
        results = self.search(kb_id, refined_query, k=5, search_type="hybrid")

        # 第三步：使用LLM生成摘要
        summary = ""
        if results:
            try:
                context_parts = []
                for i, result in enumerate(results[:3], 1):
                    context_parts.append(f"[片段{i}] {result['content'][:500]}")
                context = "\n\n".join(context_parts)

                summary_messages = [
                    {"role": "system", "content": "基于搜索结果为用户查询生成简洁的中文摘要。不要编造搜索结果中没有的信息。"},
                    {"role": "user", "content": f"用户查询：{query}\n\n搜索结果：\n{context}\n\n摘要："},
                ]
                summary = self.llm.chat(messages=summary_messages, temperature=0.3)

            except Exception as e:
                logger.warning(f"LLM生成摘要失败: {e}")
                summary = "摘要生成失败"

        return {
            "refined_query": refined_query,
            "results": results,
            "summary": summary.strip() if summary else "无搜索结果"
        }

    def rerank_results(self, query: str, results: List[dict]) -> List[dict]:
        """使用LLM对搜索结果进行重排序"""
        if not results:
            return results

        try:
            results_text = ""
            for i, result in enumerate(results):
                content_preview = result["content"][:300]
                results_text += f"\n[结果{i+1}] 内容: {content_preview}\n原始分数: {result.get('score', 0)}\n"

            rerank_messages = [
                {"role": "system", "content": "你是搜索结果相关性评估专家。根据查询对搜索结果评估相关性。"},
                {"role": "user", "content": f"查询：{query}\n\n搜索结果：\n{results_text}\n\n请对每个结果评估相关性，按格式输出（每行一个）：\n结果编号: 相关性分数(1-10)"},
            ]
            llm_output = self.llm.chat(messages=rerank_messages, temperature=0.3)

            llm_scores = {}
            for line in llm_output.strip().split("\n"):
                line = line.strip()
                match = re.match(r'结果(\d+)\s*[:：]\s*(\d+)', line)
                if match:
                    result_idx = int(match.group(1)) - 1
                    score = int(match.group(2))
                    if 0 <= result_idx < len(results):
                        llm_scores[result_idx] = score

            if llm_scores:
                for idx, llm_score in llm_scores.items():
                    normalized_llm_score = llm_score / 10.0
                    original_score = results[idx].get("score", 0)
                    results[idx]["score"] = round(
                        0.3 * original_score + 0.7 * normalized_llm_score, 4
                    )

            results.sort(key=lambda x: x.get("score", 0), reverse=True)
            return results

        except Exception as e:
            logger.error(f"LLM重排序失败: {e}")
            return sorted(results, key=lambda x: x.get("score", 0), reverse=True)
