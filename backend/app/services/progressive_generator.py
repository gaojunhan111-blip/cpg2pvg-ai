"""
渐进式内容生成器
Progressive Content Generator
"""

import asyncio
import time
import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, AsyncGenerator, Callable
from dataclasses import asdict

from app.core.logger import get_logger
from app.core.llm_client import get_llm_client
from app.services.intelligent_agent import AgentResults
from app.enums.common import AgentType
from app.schemas.pvg_schemas import (
    PVGDocument, PVGSection, PVGStructure, GenerationConfig,
    SectionContent, GenerationStatus
)
from app.enums.common import SectionType, ContentPriority
from app.services.pvg_templates import PVGTemplateManager

logger = get_logger(__name__)


class ProgressiveContentGenerator:
    """渐进式内容生成器"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.template_manager = PVGTemplateManager()
        self.llm_client = None
        self.config = GenerationConfig()

        # 添加重试配置
        self.retry_config = {
            "max_retries": 3,
            "base_delay": 1.0,
            "max_delay": 30.0,
            "backoff_factor": 2.0,
            "jitter": True
        }

        # 成本和性能统计
        self.generation_stats = {
            "total_documents": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_time": 0.0,
            "retry_attempts": 0,
            "failed_generations": 0
        }

    async def _get_llm_client(self) -> Any:
        """获取LLM客户端"""
        if self.llm_client is None:
            self.llm_client = await get_llm_client()
        return self.llm_client

    async def generate_pvg(
        self,
        agent_results: AgentResults,
        template_name: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> PVGDocument:
        """渐进式生成PVG内容"""
        document_id = f"pvg_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(f"Starting PVG generation: {document_id}")

        # 1. 准备生成配置
        if config:
            self.config = GenerationConfig(**config)

        # 2. 选择模板
        if template_name:
            template_structure = self.template_manager.get_template(template_name)
        else:
            # 从智能体结果中提取智能体类型
            agent_types = [result.agent_type for result in agent_results.results] if agent_results.results else []
            template_structure = self.template_manager.get_template(
                self.template_manager.get_template_for_agent_types(agent_types)
            )

        # 3. 创建PVG文档
        pvg_document = PVGDocument(
            document_id=document_id,
            guideline_id=agent_results.coordination_id,
            title=self._generate_title(agent_results),
            subtitle=self._generate_subtitle(agent_results),
            template_structure=template_structure
        )

        # 4. 准备章节内容
        sections_content = await self._prepare_sections_content(agent_results, template_structure)
        pvg_document.sections = self._create_pvg_sections(sections_content)

        # 5. 渐进式生成各章节
        await self._progressive_generate_sections(pvg_document, progress_callback)

        # 6. 完成文档
        pvg_document.status = GenerationStatus.COMPLETED
        pvg_document.completed_at = datetime.utcnow()
        pvg_document.update_progress()

        # 7. 更新统计
        self._update_generation_stats(pvg_document)

        self.logger.info(f"PVG generation completed: {document_id}")
        return pvg_document

    async def _prepare_sections_content(
        self,
        agent_results: AgentResults,
        template_structure: PVGStructure
    ) -> List[SectionContent]:
        """准备章节内容"""
        sections_content = []

        for section_config in template_structure.get_section_order():
            section_type = SectionType(section_config["type"])
            priority = ContentPriority(section_config["priority"])

            # 从智能体结果中提取相关内容
            context_data = self._extract_section_context(section_type, agent_results)

            section_content = SectionContent(
                section_type=section_type,
                title=section_config["title"],
                priority=priority,
                description=section_config.get("description", ""),
                required_elements=section_config.get("required_elements", []),
                optional_elements=section_config.get("optional_elements", []),
                context_data=context_data,
                estimated_tokens=section_config.get("estimated_tokens", 500),
                quality_requirements=section_config.get("quality_requirements", {})
            )

            sections_content.append(section_content)

        return sections_content

    async def _progressive_generate_sections(
        self,
        pvg_document: PVGDocument,
        progress_callback: Optional[Callable] = None
    ) -> None:
        """渐进式生成各章节"""
        # 按优先级生成章节
        high_priority_sections = [s for s in pvg_document.sections
                               if s.priority == ContentPriority.HIGH]
        medium_priority_sections = [s for s in pvg_document.sections
                                  if s.priority == ContentPriority.MEDIUM]
        low_priority_sections = [s for s in pvg_document.sections
                                if s.priority == ContentPriority.LOW]

        # 生成高优先级章节（关键内容）
        if high_priority_sections:
            await self._generate_section_batch(
                high_priority_sections,
                self.config.high_quality_llm,
                progress_callback
            )

        # 并行生成中等和低优先级章节
        if medium_priority_sections or low_priority_sections:
            remaining_sections = medium_priority_sections + low_priority_sections
            await self._generate_section_batch(
                remaining_sections,
                self.config.balanced_llm,
                progress_callback
            )

        # 更新文档进度
        pvg_document.update_progress()

    async def _generate_section_batch(
        self,
        sections: List[PVGSection],
        model: str,
        progress_callback: Optional[Callable] = None
    ) -> None:
        """批量并行生成章节 - 优化版本"""
        if not sections:
            return

        # 创建信号量限制并发数，避免过载
        semaphore = asyncio.Semaphore(min(len(sections), 5))  # 最多5个并发

        async def generate_with_semaphore(section):
            async with semaphore:
                try:
                    await self._generate_single_section(section, model)
                    return section, None
                except Exception as e:
                    self.logger.error(f"Failed to generate section {section.section_id}: {e}")
                    section.status = GenerationStatus.FAILED
                    return section, e

        # 并行执行所有章节生成
        self.logger.info(f"Starting parallel generation of {len(sections)} sections with max 5 concurrent tasks")
        tasks = [generate_with_semaphore(section) for section in sections]
        results = await asyncio.gather(*tasks)

        # 处理结果和进度回调
        for section, error in results:
            if not error and progress_callback:
                await progress_callback(section.section_id, section.status, section.content)

        self.logger.info(f"Completed parallel generation: {len([r for r in results if not r[1]])}/{len(results)} sections successful")

    async def _generate_with_retry(
        self,
        section: PVGSection,
        model: str,
        generation_func: callable
    ) -> str:
        """带重试的内容生成"""
        last_exception = None

        for attempt in range(self.retry_config["max_retries"] + 1):
            try:
                return await generation_func(section, model)

            except Exception as e:
                last_exception = e

                if attempt == self.retry_config["max_retries"]:
                    self.generation_stats["retry_attempts"] += 1
                    break

                # 计算延迟（指数退避 + 抖动）
                delay = min(
                    self.retry_config["base_delay"] *
                    (self.retry_config["backoff_factor"] ** attempt),
                    self.retry_config["max_delay"]
                )

                if self.retry_config["jitter"]:
                    delay *= (0.5 + random.random() * 0.5)  # 添加50%抖动

                self.logger.warning(
                    f"Section generation attempt {attempt + 1} failed, retrying in {delay:.1f}s: {e}"
                )
                await asyncio.sleep(delay)

        raise last_exception

    async def _generate_section_content_safe(self, section: PVGSection, model: str) -> str:
        """安全的章节内容生成（添加参数验证）"""
        # 参数验证
        if not section or not model:
            raise ValueError("Section and model cannot be empty")

        # 根据优先级选择迭代次数（限制最大值避免过度重试）
        max_iterations = {
            ContentPriority.HIGH: min(3, self.config.high_priority_iterations),
            ContentPriority.MEDIUM: min(2, self.config.medium_priority_iterations),
            ContentPriority.LOW: 1
        }

        iterations = max_iterations.get(section.priority, 1)

        # 使用超时的内容生成
        try:
            return await asyncio.wait_for(
                self._generate_section_content(section, model, iterations),
                timeout=300  # 5分钟超时
            )
        except asyncio.TimeoutError:
            raise Exception(f"Section generation timeout for {section.section_id}")

    async def _generate_single_section(self, section: PVGSection, model: str) -> None:
        """生成单个章节 - 优化版本"""
        start_time = time.time()
        section.status = GenerationStatus.IN_PROGRESS

        try:
            # 使用带重试的生成方法
            content = await self._generate_with_retry(
                section, model, self._generate_section_content_safe
            )

            # 更新章节
            section.content = content
            section.html_content = self._format_as_html(content)
            section.model_used = model
            section.generation_time = time.time() - start_time
            section.status = GenerationStatus.COMPLETED
            section.completed_at = datetime.utcnow()

            # 计算token和成本估算
            section.tokens_used = self._estimate_tokens(content)
            section.cost_estimate = self._estimate_generation_cost(model, section.tokens_used)

        except Exception as e:
            self.logger.error(f"Section generation failed {section.section_id}: {e}")
            section.status = GenerationStatus.FAILED
            self.generation_stats["failed_generations"] += 1
            # 设置错误信息，便于后续处理
            section.error_message = str(e)
            raise

    async def _generate_section_content(
        self,
        section: PVGSection,
        model: str,
        iterations: int
    ) -> str:
        """生成章节内容"""
        # 构建提示词
        prompt = self._build_section_prompt(section)

        # 选择生成策略
        if section.priority == ContentPriority.HIGH:
            return await self._high_quality_generation(prompt, model, iterations)
        elif section.priority == ContentPriority.MEDIUM:
            return await self._balanced_generation(prompt, model, iterations)
        else:
            return await self._cost_effective_generation(prompt, model, iterations)

    async def _high_quality_generation(self, prompt: str, model: str, iterations: int) -> str:
        """高质量生成（更多迭代）"""
        llm_client = await self._get_llm_client()

        for attempt in range(iterations):
            try:
                response = await llm_client.chat_completion(
                    messages=[
                        {"role": "system", "content": "You are a professional medical content writer. Create high-quality, evidence-based medical content."},
                        {"role": "user", "content": prompt}
                    ],
                    model=model,
                    max_tokens=self._get_max_tokens_for_section(),
                    temperature=0.1,
                    stream=False
                )

                if attempt == iterations - 1:
                    return response
                else:
                    # 进一步优化
                    refined_prompt = f"{prompt}\n\n请优化和改进以下内容，保持简洁明了：\n{response}"
                    prompt = refined_prompt

            except Exception as e:
                self.logger.warning(f"High quality generation attempt {attempt + 1} failed: {e}")
                if attempt == iterations - 1:
                    raise

        raise Exception("All generation attempts failed")

    async def _balanced_generation(self, prompt: str, model: str, iterations: int) -> str:
        """平衡生成"""
        llm_client = await self._get_llm_client()

        try:
            response = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Create professional medical content that is clear, concise, and evidence-based."},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                max_tokens=self._get_max_tokens_for_section(),
                temperature=0.2,
                stream=False
            )
            return response

        except Exception as e:
            self.logger.error(f"Balanced generation failed: {e}")
            raise

    async def _cost_effective_generation(self, prompt: str, model: str, iterations: int) -> str:
        """成本优化生成"""
        llm_client = await self._get_llm_client()

        try:
            response = await llm_client.chat_completion(
                messages=[
                    {"role": "system", "content": "Generate clear, essential medical content focusing on key information."},
                    {"role": "user", "content": prompt}
                ],
                model=model,
                max_tokens=self._get_max_tokens_for_section() // 2,  # 减少token使用
                temperature=0.3,
                stream=False
            )
            return response

        except Exception as e:
            self.logger.error(f"Cost effective generation failed: {e}")
            raise

    async def _stream_section_update(
        self,
        section_id: str,
        content: str,
        callback: Callable
    ) -> None:
        """流式输出章节更新"""
        try:
            # 模拟流式输出
            chunk_size = self.config.chunk_size
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                await callback(section_id, "streaming", chunk)
                await asyncio.sleep(0.01)  # 模拟流式延迟

        except Exception as e:
            self.logger.error(f"Streaming update failed for {section_id}: {e}")

    def _build_section_prompt(self, section: PVGSection) -> str:
        """构建章节生成提示词"""
        section_context = self._get_section_context(section)

        prompt = f"""
请生成{section.title}章节内容。

章节类型：{section.section_type}
优先级：{section.priority}
上下文信息：{section_context}

必需包含的要素：
{chr(10).join(f"- {element}" for element in section.metadata.get('required_elements', []))}

如果章节类型是{SectionType.KEY_RECOMMENDATIONS}，请确保：
- 包含基于证据的推荐
- 注明推荐强度和证据等级
- 明确适用人群
- 提供具体的实施建议

如果章节类型是{SectionType.TREATMENT_OPTIONS}，请确保：
- 列出一线和替代治疗方案
- 包含药物名称、剂量、用法
- 提供非药物治疗选择
- 说明治疗目标和预期效果

如果章节类型是{SectionType.SAFETY_WARNINGS}，请确保：
- 详细列出药物禁忌症
- 说明潜在的药物相互作用
- 提供不良反应监测要点
- 给出特殊人群注意事项

请用中文编写，内容要专业、准确、实用，适合医疗专业人员使用。
"""

        return prompt

    def _get_section_context(self, section: PVGSection) -> str:
        """获取章节上下文"""
        # 这里可以从section.metadata中提取上下文信息
        context = section.metadata.get("context_data", {})

        if context:
            context_str = "相关背景信息：\n"
            for key, value in context.items():
                context_str += f"- {key}: {value}\n"
            return context_str

        return "无特定背景信息"

    def _extract_section_context(self, section_type: SectionType, agent_results: AgentResults) -> Dict[str, Any]:
        """从智能体结果中提取章节上下文"""
        context = {
            "agent_results_summary": "",
            "key_findings": [],
            "recommendations": []
        }

        # 提取智能体结果的摘要
        for result in agent_results.results:
            if hasattr(result, 'summary') and result.summary:
                context["agent_results_summary"] += f"- {result.agent_type}: {result.summary}\n"

            if hasattr(result, 'key_findings') and result.key_findings:
                context["key_findings"].extend([
                    f"{finding.get('description', '')}"
                    for finding in result.key_findings
                ])

            if hasattr(result, 'recommendations') and result.recommendations:
                context["recommendations"].extend([
                    rec.get('recommendation', '')
                    for rec in result.recommendations
                ])

        return context

    def _create_pvg_sections(self, sections_content: List[SectionContent]) -> List[PVGSection]:
        """创建PVG章节"""
        sections = []

        for i, content in enumerate(sections_content):
            section = PVGSection(
                section_id=f"{content.section_type.value}_{i+1}",
                section_type=content.section_type,
                title=content.title,
                content="",  # 将在生成时填充
                priority=content.priority,
                order=i + 1,
                metadata={
                    "required_elements": content.required_elements,
                    "optional_elements": content.optional_elements,
                    "context_data": content.context_data,
                    "estimated_tokens": content.estimated_tokens,
                    "quality_requirements": content.quality_requirements
                }
            )
            sections.append(section)

        return sections

    def _generate_title(self, agent_results: AgentResults) -> str:
        """生成文档标题"""
        base_title = "临床实践指南可视化文档"

        # 从智能体结果中提取关键信息
        key_topics = []
        for result in agent_results.results:
            if hasattr(result, 'key_findings'):
                key_topics.extend([
                    finding.get('description', '')
                    for finding in result.key_findings[:3]  # 取前3个
                ])

        if key_topics:
            return f"{base_title} - {', '.join(key_topics[:2])}"

        return base_title

    def _generate_subtitle(self, agent_results: AgentResults) -> str:
        """生成文档副标题"""
        return f"基于智能体分析的{datetime.utcnow().strftime('%Y年%m月%d日')}版本"

    def _format_as_html(self, content: str) -> str:
        """格式化为HTML"""
        # 简单的HTML格式化
        html_content = content

        # 转换换换行符
        html_content = html_content.replace('\n\n', '</p><p>')
        html_content = html_content.replace('\n', '<br>')

        # 包装在HTML标签中
        html_content = f"""
        <div class="pvg-section">
            <p>{html_content}</p>
        </div>
        """

        return html_content

    def _estimate_tokens(self, content: str) -> int:
        """估算token数量"""
        # 简单估算：中文大约每个字符0.5个token
        return int(len(content) * 0.5)

    def _estimate_generation_cost(self, model: str, tokens: int) -> float:
        """估算生成成本"""
        # 简化的成本估算（实际应该根据具体模型定价）
        cost_per_1k_tokens = {
            "gpt-4": 0.03,           # $0.03 per 1K tokens
            "gpt-3.5-turbo": 0.002,  # $0.002 per 1K tokens
            "gpt-3.5-turbo-instruct": 0.0015  # $0.0015 per 1K tokens
        }

        base_cost = cost_per_1k_tokens.get(model, 0.002)
        return (tokens / 1000) * base_cost

    def _get_max_tokens_for_section(self) -> int:
        """获取章节的最大token数"""
        return self.config.max_total_tokens // 8  # 平均分配到8个章节

    def _update_generation_stats(self, document: PVGDocument) -> None:
        """更新生成统计"""
        self.generation_stats["total_documents"] += 1
        self.generation_stats["total_tokens"] += document.total_tokens
        self.generation_stats["total_cost"] += document.total_cost
        self.generation_stats["total_time"] += document.generation_time

    def get_generation_stats(self) -> Dict[str, Any]:
        """获取生成统计信息"""
        return self.generation_stats.copy()

    def reset_stats(self) -> None:
        """重置统计信息"""
        self.generation_stats = {
            "total_documents": 0,
            "total_tokens": 0,
            "total_cost": 0.0,
            "total_time": 0.0
        }


# 全局实例
progressive_generator = ProgressiveContentGenerator()


async def get_progressive_generator() -> ProgressiveContentGenerator:
    """获取渐进式内容生成器实例"""
    return progressive_generator


# 便捷函数
async def generate_pvg_document(
    agent_results: AgentResults,
    template_name: Optional[str] = None,
    enable_streaming: bool = False,
    progress_callback: Optional[Callable] = None
) -> PVGDocument:
    """生成PVG文档的便捷函数"""
    generator = await get_progressive_generator()
    return await generator.generate_pvg(
        agent_results=agent_results,
        template_name=template_name,
        config={"enable_streaming": enable_streaming},
        progress_callback=progress_callback
    )