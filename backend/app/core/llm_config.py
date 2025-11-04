"""
LLM提供商配置管理
CPG2PVG-AI System LLM Provider Configuration
"""

import asyncio
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)


class LLMProviderType(str, Enum):
    """LLM提供商类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    AZURE_OPENAI = "azure_openai"
    HUGGINGFACE = "huggingface"
    LOCAL = "local"
    MOCK = "mock"


@dataclass
class LLMModelConfig:
    """LLM模型配置"""
    name: str
    provider: LLMProviderType
    max_tokens: int = 4096
    cost_per_1k_tokens: float = 0.0
    context_length: int = 4096
    supports_functions: bool = False
    supports_vision: bool = False
    supports_streaming: bool = True
    temperature_range: tuple = (0.0, 2.0)
    description: str = ""
    tags: List[str] = field(default_factory=list)
    category: str = "general"  # general, medical, reasoning, creative


@dataclass
class LLMProviderConfig:
    """LLM提供商配置"""
    provider_type: LLMProviderType
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    api_version: Optional[str] = None
    deployment_id: Optional[str] = None  # Azure专用
    region: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit: Optional[Dict[str, int]] = None
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    priority: int = 1  # 优先级，数字越小优先级越高
    models: List[LLMModelConfig] = field(default_factory=list)


class LLMConfigManager:
    """LLM配置管理器"""

    def __init__(self):
        self.settings = get_settings()
        self._providers: Dict[str, LLMProviderConfig] = {}
        self._models: Dict[str, LLMModelConfig] = {}
        self._load_default_config()

    def _load_default_config(self):
        """加载默认配置"""
        logger.info("加载默认LLM配置...")

        # OpenAI配置
        if self.settings.OPENAI_API_KEY:
            openai_config = LLMProviderConfig(
                provider_type=LLMProviderType.OPENAI,
                name="openai",
                api_key=self.settings.OPENAI_API_KEY,
                base_url=self.settings.OPENAI_BASE_URL or "https://api.openai.com/v1",
                timeout=60,
                priority=1,
                models=[
                    LLMModelConfig(
                        name="gpt-4",
                        provider=LLMProviderType.OPENAI,
                        max_tokens=8192,
                        cost_per_1k_tokens=0.03,
                        context_length=8192,
                        supports_functions=True,
                        supports_vision=True,
                        description="GPT-4 - 高性能多模态模型",
                        tags=["reasoning", "multimodal", "functions"],
                        category="reasoning"
                    ),
                    LLMModelConfig(
                        name="gpt-4-turbo",
                        provider=LLMProviderType.OPENAI,
                        max_tokens=128000,
                        cost_per_1k_tokens=0.01,
                        context_length=128000,
                        supports_functions=True,
                        supports_vision=True,
                        description="GPT-4 Turbo - 长上下文多模态模型",
                        tags=["reasoning", "multimodal", "functions", "long-context"],
                        category="reasoning"
                    ),
                    LLMModelConfig(
                        name="gpt-3.5-turbo",
                        provider=LLMProviderType.OPENAI,
                        max_tokens=4096,
                        cost_per_1k_tokens=0.002,
                        context_length=4096,
                        supports_functions=True,
                        description="GPT-3.5 Turbo - 快速响应模型",
                        tags=["fast", "functions"],
                        category="general"
                    )
                ]
            )
            self._providers["openai"] = openai_config
            for model in openai_config.models:
                self._models[f"openai:{model.name}"] = model

        # Anthropic配置
        if self.settings.ANTHROPIC_API_KEY:
            anthropic_config = LLMProviderConfig(
                provider_type=LLMProviderType.ANTHROPIC,
                name="anthropic",
                api_key=self.settings.ANTHROPIC_API_KEY,
                base_url=self.settings.ANTHROPIC_BASE_URL or "https://api.anthropic.com/v1",
                timeout=60,
                priority=2,
                headers={"anthropic-version": "2023-06-01"},
                models=[
                    LLMModelConfig(
                        name="claude-3-sonnet-20240229",
                        provider=LLMProviderType.ANTHROPIC,
                        max_tokens=200000,
                        cost_per_1k_tokens=0.015,
                        context_length=200000,
                        description="Claude 3 Sonnet - 均衡性能模型",
                        tags=["reasoning", "long-context", "safety"],
                        category="reasoning"
                    ),
                    LLMModelConfig(
                        name="claude-3-haiku-20240307",
                        provider=LLMProviderType.ANTHROPIC,
                        max_tokens=200000,
                        cost_per_1k_tokens=0.00025,
                        context_length=200000,
                        description="Claude 3 Haiku - 快速响应模型",
                        tags=["fast", "long-context", "cost-effective"],
                        category="general"
                    ),
                    LLMModelConfig(
                        name="claude-3-opus-20240229",
                        provider=LLMProviderType.ANTHROPIC,
                        max_tokens=200000,
                        cost_per_1k_tokens=0.075,
                        context_length=200000,
                        description="Claude 3 Opus - 最高性能模型",
                        tags=["reasoning", "long-context", "high-quality"],
                        category="reasoning"
                    )
                ]
            )
            self._providers["anthropic"] = anthropic_config
            for model in anthropic_config.models:
                self._models[f"anthropic:{model.name}"] = model

        # Mock配置（测试用）
        mock_config = LLMProviderConfig(
            provider_type=LLMProviderType.MOCK,
            name="mock",
            enabled=True,
            priority=99,
            models=[
                LLMModelConfig(
                    name="mock-model",
                    provider=LLMProviderType.MOCK,
                    max_tokens=4096,
                    cost_per_1k_tokens=0.0,
                    description="Mock模型 - 用于测试",
                    tags=["test", "mock"],
                    category="general"
                )
            ]
        )
        self._providers["mock"] = mock_config
        for model in mock_config.models:
            self._models[f"mock:{model.name}"] = model

        logger.info(f"已加载 {len(self._providers)} 个提供商, {len(self._models)} 个模型")

    def get_provider(self, provider_name: str) -> Optional[LLMProviderConfig]:
        """获取提供商配置"""
        return self._providers.get(provider_name)

    def get_model(self, model_key: str) -> Optional[LLMModelConfig]:
        """获取模型配置"""
        return self._models.get(model_key)

    def get_providers(self, enabled_only: bool = True) -> List[LLMProviderConfig]:
        """获取提供商列表"""
        providers = list(self._providers.values())
        if enabled_only:
            providers = [p for p in providers if p.enabled]
        # 按优先级排序
        providers.sort(key=lambda x: x.priority)
        return providers

    def get_models(
        self,
        provider: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True
    ) -> List[LLMModelConfig]:
        """获取模型列表"""
        models = list(self._models.values())

        # 过滤提供商
        if provider:
            models = [m for m in models if m.provider.value == provider]

        # 过滤分类
        if category:
            models = [m for m in models if m.category == category]

        # 过滤标签
        if tags:
            models = [m for m in models if any(tag in m.tags for tag in tags)]

        # 过滤启用的提供商
        if enabled_only:
            enabled_providers = {p.name for p in self.get_providers(enabled_only=True)}
            models = [m for m in models if m.provider.value in enabled_providers]

        return models

    def get_best_model(
        self,
        category: Optional[str] = None,
        max_cost: Optional[float] = None,
        min_context: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[LLMModelConfig]:
        """获取最佳模型推荐"""
        models = self.get_models(category=category, tags=tags)

        # 过滤成本
        if max_cost is not None:
            models = [m for m in models if m.cost_per_1k_tokens <= max_cost]

        # 过滤上下文长度
        if min_context is not None:
            models = [m for m in models if m.context_length >= min_context]

        if not models:
            return None

        # 按优先级和成本选择
        # 优先选择优先级高的提供商，然后选择成本合理的模型
        providers = self.get_providers()
        provider_priority = {p.name: i for i, p in enumerate(providers)}

        def model_score(model: LLMModelConfig) -> tuple:
            priority = provider_priority.get(model.provider.value, 999)
            # 成本越低越好（成本权重）
            cost_score = -model.cost_per_1k_tokens
            # 上下文长度越大越好
            context_score = model.context_length / 1000000
            return (priority, cost_score, context_score)

        return max(models, key=model_score)

    def add_provider(self, provider_config: LLMProviderConfig):
        """添加提供商配置"""
        self._providers[provider_config.name] = provider_config
        for model in provider_config.models:
            self._models[f"{provider_config.name}:{model.name}"] = model
        logger.info(f"已添加提供商: {provider_config.name}")

    def remove_provider(self, provider_name: str) -> bool:
        """移除提供商配置"""
        if provider_name in self._providers:
            # 移除相关模型
            models_to_remove = [
                key for key, model in self._models.items()
                if model.provider.value == provider_name
            ]
            for key in models_to_remove:
                del self._models[key]

            del self._providers[provider_name]
            logger.info(f"已移除提供商: {provider_name}")
            return True
        return False

    def update_provider(self, provider_name: str, **kwargs):
        """更新提供商配置"""
        if provider_name in self._providers:
            provider = self._providers[provider_name]
            for key, value in kwargs.items():
                if hasattr(provider, key):
                    setattr(provider, key, value)
            logger.info(f"已更新提供商配置: {provider_name}")

    def enable_provider(self, provider_name: str):
        """启用提供商"""
        if provider_name in self._providers:
            self._providers[provider_name].enabled = True
            logger.info(f"已启用提供商: {provider_name}")

    def disable_provider(self, provider_name: str):
        """禁用提供商"""
        if provider_name in self._providers:
            self._providers[provider_name].enabled = False
            logger.info(f"已禁用提供商: {provider_name}")

    def get_cost_estimates(self, prompt_tokens: int, completion_tokens: int) -> Dict[str, float]:
        """获取成本估算"""
        estimates = {}
        for model_key, model in self._models.items():
            # 简单的成本计算（实际可能因提供商而异）
            prompt_cost = (prompt_tokens / 1000) * model.cost_per_1k_tokens
            completion_cost = (completion_tokens / 1000) * model.cost_per_1k_tokens
            total_cost = prompt_cost + completion_cost
            estimates[model_key] = total_cost
        return estimates

    def validate_config(self) -> List[str]:
        """验证配置"""
        errors = []

        for provider_name, provider in self._providers.items():
            if provider.enabled:
                # 检查必需的API密钥
                if provider.provider_type not in [LLMProviderType.MOCK, LLMProviderType.LOCAL]:
                    if not provider.api_key:
                        errors.append(f"Provider {provider_name}: API密钥缺失")

                # 检查模型配置
                if not provider.models:
                    errors.append(f"Provider {provider_name}: 未配置模型")

        return errors

    def export_config(self) -> Dict[str, Any]:
        """导出配置（隐藏敏感信息）"""
        config = {
            "providers": {},
            "models": {}
        }

        for name, provider in self._providers.items():
            provider_data = {
                "provider_type": provider.provider_type.value,
                "name": provider.name,
                "base_url": provider.base_url,
                "timeout": provider.timeout,
                "max_retries": provider.max_retries,
                "retry_delay": provider.retry_delay,
                "rate_limit": provider.rate_limit,
                "headers": {k: v for k, v in provider.headers.items() if "key" not in k.lower()},
                "params": provider.params,
                "enabled": provider.enabled,
                "priority": provider.priority,
                "has_api_key": bool(provider.api_key)
            }
            config["providers"][name] = provider_data

        for key, model in self._models.items():
            model_data = {
                "name": model.name,
                "provider": model.provider.value,
                "max_tokens": model.max_tokens,
                "cost_per_1k_tokens": model.cost_per_1k_tokens,
                "context_length": model.context_length,
                "supports_functions": model.supports_functions,
                "supports_vision": model.supports_vision,
                "supports_streaming": model.supports_streaming,
                "temperature_range": model.temperature_range,
                "description": model.description,
                "tags": model.tags,
                "category": model.category
            }
            config["models"][key] = model_data

        return config

    def save_config(self, file_path: Union[str, Path]):
        """保存配置到文件"""
        config = self.export_config()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        logger.info(f"配置已保存到: {file_path}")


# 全局配置管理器实例
llm_config_manager = LLMConfigManager()


def get_llm_config_manager() -> LLMConfigManager:
    """获取LLM配置管理器实例"""
    return llm_config_manager


# 预定义的模型选择策略
class ModelSelectionStrategy:
    """模型选择策略"""

    @staticmethod
    def fastest() -> Optional[LLMModelConfig]:
        """最快响应策略"""
        return llm_config_manager.get_best_model(tags=["fast"])

    @staticmethod
    def cost_effective() -> Optional[LLMModelConfig]:
        """成本效益策略"""
        return llm_config_manager.get_best_model(max_cost=0.01)

    @staticmethod
    def highest_quality() -> Optional[LLMModelConfig]:
        """最高质量策略"""
        return llm_config_manager.get_best_model(category="reasoning", tags=["high-quality"])

    @staticmethod
    def medical_specialized() -> Optional[LLMModelConfig]:
        """医学专业策略"""
        return llm_config_manager.get_best_model(category="medical")

    @staticmethod
    def long_context() -> Optional[LLMModelConfig]:
        """长上下文策略"""
        return llm_config_manager.get_best_model(min_context=100000, tags=["long-context"])

    @staticmethod
    def multimodal() -> Optional[LLMModelConfig]:
        """多模态策略"""
        return llm_config_manager.get_best_model(tags=["multimodal"])


# 便捷函数
def get_available_models(category: Optional[str] = None) -> List[LLMModelConfig]:
    """获取可用模型列表"""
    return llm_config_manager.get_models(category=category)


def get_model_by_name(model_name: str, provider: Optional[str] = None) -> Optional[LLMModelConfig]:
    """根据名称获取模型"""
    if provider:
        model_key = f"{provider}:{model_name}"
    else:
        # 查找所有提供商中的模型
        for key, model in llm_config_manager._models.items():
            if model.name == model_name:
                return model
        return None

    return llm_config_manager.get_model(model_key)


def recommend_model_for_task(task_type: str, **kwargs) -> Optional[LLMModelConfig]:
    """为任务推荐模型"""
    task_strategies = {
        "reasoning": ModelSelectionStrategy.highest_quality,
        "generation": ModelSelectionStrategy.cost_effective,
        "analysis": ModelSelectionStrategy.fastest,
        "medical": ModelSelectionStrategy.medical_specialized,
        "translation": ModelSelectionStrategy.cost_effective,
        "summary": ModelSelectionStrategy.fastest,
        "classification": ModelSelectionStrategy.fastest,
        "multimodal": ModelSelectionStrategy.multimodal,
        "long_context": ModelSelectionStrategy.long_context
    }

    strategy = task_strategies.get(task_type, ModelSelectionStrategy.cost_effective)
    return strategy()