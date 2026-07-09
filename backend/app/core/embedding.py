"""
Embedding 服务模块
使用 LangChain OpenAIEmbeddings 配合 DashScope text-embedding-v2 模型
"""

from langchain_openai import OpenAIEmbeddings

from app.config import settings

# 全局缓存 Embedding 实例，避免重复创建
_embeddings_instance: OpenAIEmbeddings | None = None


def get_embeddings() -> OpenAIEmbeddings:
    """
    获取 Embedding 模型实例（单例模式）

    使用 DashScope 的 text-embedding-v2 模型（默认1536维）。
    注意：需禁用 LangChain 的 tiktoken 分组分块功能，
    因为 DashScope API 不接受 tokenized input 格式。

    Returns:
        OpenAIEmbeddings 实例
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        _embeddings_instance = OpenAIEmbeddings(
            model="text-embedding-v2",
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            # 关键：禁用 tiktoken 分组，直接发送原始文本
            check_embedding_ctx_length=False,
        )
    return _embeddings_instance
