"""
LLM客户端实现 - 改进版
Enhanced LLM Client Implementation
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union, Callable
from abc import ABC, abstractmethod
import httpx
import json
from datetime import datetime
from enum import Enum
import uuid
from dataclasses import dataclass, asdict

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.error_handling import CPG2PVGException, retry, API_RETRY_CONFIG, ExternalAPIError

logger = get_logger(__name__)
settings = get_settings()


class LLMProvider(str, Enum):
    """LLM提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    LOCAL = "local"
    MOCK = "mock"


class MessageRole(str, Enum):
    """消息角色"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    FUNCTION = "function"


@dataclass
class ChatMessage:
    """聊天消息"""
    role: MessageRole
    content: str
    name: Optional[str] = None
    function_call: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    """LLM响应"""
    content: str
    model: str
    usage: Dict[str, int]
    finish_reason: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass
class ModelInfo:
    """模型信息"""
    id: str
    name: str
    provider: LLMProvider
    max_tokens: int
    context_length: int
    cost_per_token: float
    capabilities: List[str]


class BaseLLMProvider(ABC):
    """LLM提供商基类"""

    def __init__(self, api_key: str, base_url: str = None):
        self.api_key = api_key
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(60.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    @abstractmethod
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """聊天完成接口"""
        pass

    @abstractmethod
    async def get_model_info(self, model: str) -> ModelInfo:
        """获取模型信息"""
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelInfo]:
        """列出可用模型"""
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()


class OpenAIProvider(BaseLLMProvider):
    """OpenAI提供商"""

    def __init__(self):
        super().__init__(
            api_key=getattr(settings, 'OPENAI_API_KEY', ''),
            base_url=getattr(settings, 'OPENAI_BASE_URL', 'https://api.openai.com/v1')
        )
        self.default_model = getattr(settings, 'DEFAULT_LLM_MODEL', 'gpt-3.5-turbo')

    @retry(config=API_RETRY_CONFIG)
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """OpenAI聊天完成"""
        try:
            if not self.api_key:
                raise CPG2PVGException("OpenAI API密钥未配置")

            model = model or self.default_model

            # 转换消息格式
            openai_messages = []
            for msg in messages:
                openai_msg = {
                    "role": msg.role.value,
                    "content": msg.content
                }
                if msg.name:
                    openai_msg["name"] = msg.name
                if msg.function_call:
                    openai_msg["function_call"] = msg.function_call
                openai_messages.append(openai_msg)

            # 构建请求
            request_data = {
                "model": model,
                "messages": openai_messages,
                "max_tokens": max_tokens or 1000,
                "temperature": temperature or 0.7,
                **kwargs
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 发送请求
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                json=request_data,
                headers=headers
            )
            response.raise_for_status()

            data = response.json()
            choice = data["choices"][0]
            message = choice["message"]

            return LLMResponse(
                content=message.get("content", ""),
                model=data["model"],
                usage=data.get("usage", {}),
                finish_reason=choice.get("finish_reason"),
                metadata={
                    "provider": "openai",
                    "response_id": data.get("id"),
                    "created": data.get("created"),
                    "object": data.get("object")
                }
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"OpenAI API错误: {e.response.status_code} - {e.response.text}")
            raise ExternalAPIError(
                message=f"OpenAI API请求失败: {e.response.status_code}",
                api_name="OpenAI",
                status_code=e.response.status_code
            )
        except Exception as e:
            logger.error(f"OpenAI聊天完成失败: {str(e)}")
            raise CPG2PVGException(
                message=f"LLM调用失败: {str(e)}",
                category="external_api",
                severity="medium"
            )

    async def get_model_info(self, model: str) -> ModelInfo:
        """获取OpenAI模型信息"""
        model_configs = {
            "gpt-4": ModelInfo(
                id="gpt-4",
                name="GPT-4",
                provider=LLMProvider.OPENAI,
                max_tokens=8192,
                context_length=8192,
                cost_per_token=0.00003,
                capabilities=["chat", "function_calling", "code_generation"]
            ),
            "gpt-4-turbo": ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider=LLMProvider.OPENAI,
                max_tokens=128000,
                context_length=128000,
                cost_per_token=0.00001,
                capabilities=["chat", "function_calling", "code_generation", "vision"]
            ),
            "gpt-3.5-turbo": ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider=LLMProvider.OPENAI,
                max_tokens=4096,
                context_length=4096,
                cost_per_token=0.000002,
                capabilities=["chat", "function_calling", "code_generation"]
            )
        }
        return model_configs.get(model, model_configs.get("gpt-3.5-turbo"))

    async def list_models(self) -> List[ModelInfo]:
        """列出OpenAI模型"""
        return [
            await self.get_model_info("gpt-4"),
            await self.get_model_info("gpt-4-turbo"),
            await self.get_model_info("gpt-3.5-turbo")
        ]


class AnthropicProvider(BaseLLMProvider):
    """Anthropic (Claude) 提供商"""

    def __init__(self):
        super().__init__(
            api_key=getattr(settings, 'ANTHROPIC_API_KEY', ''),
            base_url="https://api.anthropic.com/v1"
        )
        self.default_model = getattr(settings, 'DEFAULT_ANTHROPIC_MODEL', 'claude-3-sonnet-20240229')

    @retry(config=API_RETRY_CONFIG)
    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Anthropic聊天完成"""
        try:
            if not self.api_key:
                raise CPG2PVGException("Anthropic API密钥未配置")

            model = model or self.default_model

            # 转换消息格式 (Anthropic使用不同的格式)
            system_message = ""
            conversation_messages = []

            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant",
                        "content": msg.content
                    })

            request_data = {
                "model": model,
                "max_tokens": max_tokens or 1000,
                "temperature": temperature or 0.7,
                "messages": conversation_messages,
                **kwargs
            }

            if system_message:
                request_data["system"] = system_message

            headers = {
                "x-api-key": self.api_key,
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            }

            response = await self.client.post(
                f"{self.base_url}/messages",
                json=request_data,
                headers=headers
            )
            response.raise_for_status()

            data = response.json()

            return LLMResponse(
                content=data["content"][0]["text"],
                model=data["model"],
                usage=data.get("usage", {}),
                finish_reason=data.get("stop_reason"),
                metadata={
                    "provider": "anthropic",
                    "response_id": data.get("id"),
                    "type": data.get("type")
                }
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Anthropic API错误: {e.response.status_code} - {e.response.text}")
            raise ExternalAPIError(
                message=f"Anthropic API请求失败: {e.response.status_code}",
                api_name="Anthropic",
                status_code=e.response.status_code
            )
        except Exception as e:
            logger.error(f"Anthropic聊天完成失败: {str(e)}")
            raise CPG2PVGException(
                message=f"LLM调用失败: {str(e)}",
                category="external_api",
                severity="medium"
            )

    async def get_model_info(self, model: str) -> ModelInfo:
        """获取Anthropic模型信息"""
        model_configs = {
            "claude-3-opus-20240229": ModelInfo(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                provider=LLMProvider.ANTHROPIC,
                max_tokens=4096,
                context_length=200000,
                cost_per_token=0.000075,
                capabilities=["chat", "vision", "code_generation", "analysis"]
            ),
            "claude-3-sonnet-20240229": ModelInfo(
                id="claude-3-sonnet-20240229",
                name="Claude 3 Sonnet",
                provider=LLMProvider.ANTHROPIC,
                max_tokens=4096,
                context_length=200000,
                cost_per_token=0.000015,
                capabilities=["chat", "vision", "code_generation", "analysis"]
            ),
            "claude-3-haiku-20240307": ModelInfo(
                id="claude-3-haiku-20240307",
                name="Claude 3 Haiku",
                provider=LLMProvider.ANTHROPIC,
                max_tokens=4096,
                context_length=200000,
                cost_per_token=0.00000025,
                capabilities=["chat", "vision", "fast_response"]
            )
        }
        return model_configs.get(model, model_configs.get("claude-3-sonnet-20240229"))

    async def list_models(self) -> List[ModelInfo]:
        """列出Anthropic模型"""
        return [
            await self.get_model_info("claude-3-opus-20240229"),
            await self.get_model_info("claude-3-sonnet-20240229"),
            await self.get_model_info("claude-3-haiku-20240307")
        ]


class MockLLMProvider(BaseLLMProvider):
    """Mock LLM提供商 - 用于测试和开发"""

    def __init__(self):
        super().__init__("mock-key", "mock-url")
        self.response_templates = {
            "analysis": "基于提供的医学指南内容，我进行了详细分析。该指南包含了全面的临床实践建议，涵盖了诊断标准、治疗流程和随访管理等方面。",
            "summary": "这是一份关于医疗实践的指南文档，主要内容包括患者评估、治疗方案和临床决策建议。",
            "recommendation": "根据现有证据和研究结果，建议采用标准化的临床处理流程，确保患者获得最佳的医疗服务。",
            "extraction": "已成功提取文档中的关键信息，包括推荐意见、证据等级和临床实践要点。"
        }

    async def chat_completion(
        self,
        messages: List[ChatMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Mock聊天完成"""
        await asyncio.sleep(0.5)  # 模拟网络延迟

        # 基于最后一条用户消息生成响应
        user_content = ""
        for msg in reversed(messages):
            if msg.role == MessageRole.USER:
                user_content = msg.content.lower()
                break

        # 根据用户输入选择合适的响应模板
        response_content = self.response_templates["summary"]
        if "分析" in user_content or "analysis" in user_content:
            response_content = self.response_templates["analysis"]
        elif "推荐" in user_content or "recommendation" in user_content:
            response_content = self.response_templates["recommendation"]
        elif "提取" in user_content or "extraction" in user_content:
            response_content = self.response_templates["extraction"]

        return LLMResponse(
            content=response_content,
            model="mock-model",
            usage={
                "prompt_tokens": len(" ".join([msg.content for msg in messages])) // 4,
                "completion_tokens": len(response_content) // 4,
                "total_tokens": (len(" ".join([msg.content for msg in messages])) + len(response_content)) // 4
            },
            finish_reason="stop",
            metadata={
                "provider": "mock",
                "response_id": f"mock_{uuid.uuid4().hex[:8]}",
                "simulated": True
            }
        )

    async def get_model_info(self, model: str) -> ModelInfo:
        """获取Mock模型信息"""
        return ModelInfo(
            id="mock-model",
            name="Mock LLM Model",
            provider=LLMProvider.MOCK,
            max_tokens=10000,
            context_length=10000,
            cost_per_token=0.0,
            capabilities=["chat", "analysis", "summarization"]
        )

    async def list_models(self) -> List[ModelInfo]:
        """列出Mock模型"""
        return [await self.get_model_info("mock-model")]


class LLMClient:
    """LLM客户端主类"""

    def __init__(self):
        self.providers = {}
        self.current_provider = None
        self._initialize_providers()

    def _initialize_providers(self):
        """初始化LLM提供商"""
        try:
            # 初始化各个提供商
            if getattr(settings, 'ANTHROPIC_API_KEY', None):
                self.providers[LLMProvider.ANTHROPIC] = AnthropicProvider()
                logger.info("Anthropic提供商初始化成功")

            if getattr(settings, 'OPENAI_API_KEY', None):
                self.providers[LLMProvider.OPENAI] = OpenAIProvider()
                logger.info("OpenAI提供商初始化成功")

            # 总是包含Mock提供商作为后备
            self.providers[LLMProvider.MOCK] = MockLLMProvider()
            logger.info("Mock提供商初始化成功")

            # 设置默认提供商
            default_provider = getattr(settings, 'DEFAULT_LLM_PROVIDER', 'mock')
            self.current_provider = self.providers.get(
                LLMProvider(default_provider),
                self.providers[LLMProvider.MOCK]
            )

            logger.info(f"LLM客户端初始化完成，默认提供商: {type(self.current_provider).__name__}")

        except Exception as e:
            logger.error(f"LLM提供商初始化失败: {str(e)}")
            # 确保至少有Mock提供商可用
            self.providers[LLMProvider.MOCK] = MockLLMProvider()
            self.current_provider = self.providers[LLMProvider.MOCK]

    def set_provider(self, provider_name: Union[str, LLMProvider]):
        """设置当前使用的提供商"""
        provider = self.providers.get(LLMProvider(provider_name))
        if not provider:
            raise ValueError(f"不支持的提供商: {provider_name}")
        self.current_provider = provider
        logger.info(f"切换到提供商: {type(provider).__name__}")

    @retry(config=API_RETRY_CONFIG)
    async def chat_completion(
        self,
        messages: List[Union[ChatMessage, Dict[str, str]]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        聊天完成

        Args:
            messages: 聊天消息列表
            max_tokens: 最大生成token数
            temperature: 温度参数
            model: 模型名称
            provider: 指定提供商
            **kwargs: 其他参数

        Returns:
            LLMResponse: LLM响应
        """
        try:
            # 选择提供商
            current_provider = self.current_provider
            if provider:
                provider_instance = self.providers.get(LLMProvider(provider))
                if not provider_instance:
                    raise ValueError(f"不支持的提供商: {provider}")
                current_provider = provider_instance

            # 转换消息格式
            chat_messages = []
            for msg in messages:
                if isinstance(msg, dict):
                    chat_msg = ChatMessage(
                        role=MessageRole(msg.get("role", "user")),
                        content=msg.get("content", ""),
                        name=msg.get("name"),
                        function_call=msg.get("function_call")
                    )
                else:
                    chat_msg = msg
                chat_messages.append(chat_msg)

            logger.info("开始LLM聊天完成", extra_data={
                "provider": type(current_provider).__name__,
                "model": model,
                "message_count": len(chat_messages),
                "max_tokens": max_tokens
            })

            # 调用提供商
            response = await current_provider.chat_completion(
                messages=chat_messages,
                max_tokens=max_tokens,
                temperature=temperature,
                model=model,
                **kwargs
            )

            logger.info("LLM聊天完成成功", extra_data={
                "model": response.model,
                "usage": response.usage,
                "finish_reason": response.finish_reason
            })

            return response

        except Exception as e:
            logger.error(f"LLM聊天完成失败: {str(e)}")
            # 如果当前提供商失败，尝试切换到Mock提供商
            if provider != "mock" and self.current_provider != self.providers[LLMProvider.MOCK]:
                logger.info("切换到Mock提供商重试")
                return await self.chat_completion(
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    model=model,
                    provider="mock",
                    **kwargs
                )
            raise

    async def get_model_info(self, model: str, provider: Optional[str] = None) -> ModelInfo:
        """获取模型信息"""
        current_provider = self.current_provider
        if provider:
            provider_instance = self.providers.get(LLMProvider(provider))
            if provider_instance:
                current_provider = provider_instance

        return await current_provider.get_model_info(model)

    async def list_models(self, provider: Optional[str] = None) -> List[ModelInfo]:
        """列出可用模型"""
        if provider:
            provider_instance = self.providers.get(LLMProvider(provider))
            if provider_instance:
                return await provider_instance.list_models()
            return []

        # 返回所有提供商的模型
        all_models = []
        for provider_instance in self.providers.values():
            try:
                models = await provider_instance.list_models()
                all_models.extend(models)
            except Exception as e:
                logger.warning(f"获取提供商模型列表失败: {str(e)}")
                continue

        return all_models

    async def analyze_medical_text(
        self,
        text: str,
        analysis_type: str = "summary",
        context: Optional[str] = None
    ) -> LLMResponse:
        """
        医学文本分析专用方法

        Args:
            text: 要分析的医学文本
            analysis_type: 分析类型 (summary, extraction, analysis, recommendation)
            context: 可选的上下文信息

        Returns:
            LLMResponse: 分析结果
        """
        system_prompts = {
            "summary": "你是一个专业的医学文本分析专家。请对提供的医学指南或临床文档进行准确的总结，提取关键信息并保持专业性和准确性。",
            "extraction": "你是一个专业的医学信息提取专家。请从提供的医学文档中准确提取结构化的关键信息，包括推荐意见、证据等级、适应症等。",
            "analysis": "你是一个资深的医学分析专家。请对提供的医学指南进行深入分析，评估其科学性、适用性和临床价值。",
            "recommendation": "你是一个循证医学专家。请基于提供的医学内容，生成清晰、可操作的临床实践建议。"
        }

        system_prompt = system_prompts.get(analysis_type, system_prompts["summary"])

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
            ChatMessage(role=MessageRole.USER, content=f"请分析以下医学内容：\n\n{text}")
        ]

        if context:
            messages.insert(1, ChatMessage(
                role=MessageRole.USER,
                content=f"背景信息：{context}"
            ))

        return await self.chat_completion(
            messages=messages,
            max_tokens=2000,
            temperature=0.3  # 医学内容需要较低的随机性
        )

    async def close(self):
        """关闭客户端"""
        for provider in self.providers.values():
            if hasattr(provider, 'client'):
                await provider.client.aclose()


# 全局LLM客户端实例
llm_client = LLMClient()


async def get_llm_client() -> LLMClient:
    """获取LLM客户端实例"""
    return llm_client