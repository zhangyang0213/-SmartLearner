"""
大语言模型客户端 - 基于 LangChain ChatOpenAI 对接阿里百炼 DashScope API
"""

from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm(temperature: float = 0.7, streaming: bool = False) -> ChatOpenAI:
    """
    获取主用 LLM 实例（qwen-plus）

    Args:
        temperature: 生成温度
        streaming: 是否启用流式输出

    Returns:
        配置为 DashScope qwen-plus 的 ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=settings.LLM_MODEL,
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        max_tokens=4096,
    )


def get_fast_llm(temperature: float = 0.3, streaming: bool = False) -> ChatOpenAI:
    """
    获取快速 LLM 实例（qwen-turbo），用于不需要深度推理的场景

    Args:
        temperature: 生成温度
        streaming: 是否启用流式输出

    Returns:
        配置为 DashScope qwen-turbo 的 ChatOpenAI 实例
    """
    return ChatOpenAI(
        model=settings.LLM_MODEL_FAST,
        api_key=settings.DASHSCOPE_API_KEY,
        base_url=settings.DASHSCOPE_BASE_URL,
        temperature=temperature,
        streaming=streaming,
        max_tokens=2048,
    )


class LLMClient:
    """
    高级 LLM 客户端，支持同步调用、流式调用和 JSON 模式
    封装 LangChain ChatOpenAI，提供更便捷的调用接口
    """

    def __init__(self, model: str | None = None, temperature: float = 0.7):
        self.model = model or settings.LLM_MODEL
        self.temperature = temperature
        self._llm = ChatOpenAI(
            model=self.model,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=temperature,
            max_tokens=4096,
        )

    def chat(self, messages: list[dict]) -> str:
        """
        同步调用 LLM 进行对话

        Args:
            messages: 消息列表 [{"role": "system/user/assistant", "content": "..."}]

        Returns:
            LLM 生成的文本内容
        """
        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        response = self._llm.invoke(lc_messages)
        return response.content

    def chat_json(self, messages: list[dict], temperature: float = 0.3) -> dict:
        """
        调用 LLM 并解析 JSON 响应

        Args:
            messages: 消息列表
            temperature: 生成温度（默认较低以保证 JSON 格式）

        Returns:
            解析后的字典
        """
        import json
        import re

        # 使用较低温度的临时 LLM
        json_llm = ChatOpenAI(
            model=self.model,
            api_key=settings.DASHSCOPE_API_KEY,
            base_url=settings.DASHSCOPE_BASE_URL,
            temperature=temperature,
            max_tokens=4096,
        )

        from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

        lc_messages = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                lc_messages.append(SystemMessage(content=content))
            elif role == "assistant":
                lc_messages.append(AIMessage(content=content))
            else:
                lc_messages.append(HumanMessage(content=content))

        response = json_llm.invoke(lc_messages)
        text = response.content

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试从文本中提取 JSON
            json_match = re.search(r'\{[\s\S]*\}', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            # 最后尝试提取数组
            json_match = re.search(r'\[[\s\S]*\]', text)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            raise ValueError(f"无法解析LLM返回的JSON: {text[:200]}")
