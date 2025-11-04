"""
智能体协调器服务
Agent Orchestrator Service
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid

from app.core.logger import get_logger
from app.services.intelligent_agent import (
    AgentResult, AgentStatus, ProcessingStrategy, AgentType
)
from app.services.medical_agents import create_medical_agent

logger = get_logger(__name__)


class AgentOrchestrator:
    """智能体协调器"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.agents = {
            AgentType.DIAGNOSIS: create_medical_agent(AgentType.DIAGNOSIS),
            AgentType.TREATMENT: create_medical_agent(AgentType.TREATMENT),
            AgentType.PREVENTION: create_medical_agent(AgentType.PREVENTION),
            AgentType.MONITORING: create_medical_agent(AgentType.MONITORING),
            AgentType.SPECIAL_POPULATIONS: create_medical_agent(AgentType.SPECIAL_POPULATIONS)
        }

    async def orchestrate_processing(
        self,
        content_data: Dict[str, Any],
        strategy: ProcessingStrategy = ProcessingStrategy.PARALLEL,
        agent_types: Optional[List[AgentType]] = None
    ) -> Dict[str, Any]:
        """协调智能体处理"""
        coordination_id = str(uuid.uuid4())
        start_time = datetime.utcnow()

        self.logger.info(f"Starting orchestration {coordination_id} with strategy: {strategy}")

        try:
            # 1. 准备相关内容
            relevant_contents = await self._prepare_relevant_contents(content_data, agent_types)

            # 2. 执行智能体处理
            agent_results = await self._execute_agent_processing(
                relevant_contents, strategy, coordination_id
            )

            # 3. 整合结果
            integrated_result = await self._integrate_results(agent_results, coordination_id)

            # 4. 质量评估
            quality_metrics = await self._assess_quality(integrated_result)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            final_result = {
                "coordination_id": coordination_id,
                "status": "completed",
                "agent_results": [result.__dict__ for result in agent_results],
                "integrated_result": integrated_result,
                "quality_metrics": quality_metrics,
                "processing_strategy": strategy,
                "processing_time": processing_time,
                "agents_count": len(agent_results),
                "successful_agents": len([r for r in agent_results if r.status == AgentStatus.COMPLETED])
            }

            self.logger.info(f"Orchestration {coordination_id} completed successfully")
            return final_result

        except Exception as e:
            self.logger.error(f"Orchestration {coordination_id} failed: {e}")
            return {
                "coordination_id": coordination_id,
                "status": "failed",
                "error": str(e),
                "processing_time": (datetime.utcnow() - start_time).total_seconds()
            }

    async def _prepare_relevant_contents(
        self,
        content_data: Dict[str, Any],
        agent_types: Optional[List[AgentType]]
    ) -> List[tuple]:
        """准备相关内容"""
        from app.services.intelligent_agent import RelevantContent

        if agent_types is None:
            agent_types = list(AgentType)

        relevant_contents = []
        text_content = content_data.get("content", "")
        content_id = content_data.get("content_id", str(uuid.uuid4()))

        for agent_type in agent_types:
            content = RelevantContent(
                content_id=f"{content_id}_{agent_type.value}",
                agent_type=agent_type,
                text_segments=[(text_content, "main", "text")],
                relevance_score=self._calculate_relevance_score(agent_type, text_content),
                priority=self._get_agent_priority(agent_type)
            )
            relevant_contents.append((agent_type, content))

        return relevant_contents

    async def _execute_agent_processing(
        self,
        relevant_contents: List[tuple],
        strategy: ProcessingStrategy,
        coordination_id: str
    ) -> List[AgentResult]:
        """执行智能体处理"""
        self.logger.info(f"Executing agent processing with strategy: {strategy}")

        if strategy == ProcessingStrategy.PARALLEL:
            return await self._execute_parallel_processing(relevant_contents)
        elif strategy == ProcessingStrategy.SEQUENTIAL:
            return await self._execute_sequential_processing(relevant_contents)
        else:
            return await self._execute_parallel_processing(relevant_contents)

    async def _execute_parallel_processing(
        self,
        relevant_contents: List[tuple]
    ) -> List[AgentResult]:
        """并行处理"""
        tasks = []
        for agent_type, content in relevant_contents:
            if agent_type in self.agents:
                task = self.agents[agent_type].process_with_fallback(content)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"Agent processing failed: {result}")
                # 创建失败结果
                failed_result = AgentResult(
                    result_id=f"failed_{i}",
                    agent_type=relevant_contents[i][0] if i < len(relevant_contents) else AgentType.DIAGNOSIS,
                    status=AgentStatus.FAILED,
                    error_message=str(result)
                )
                processed_results.append(failed_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _execute_sequential_processing(
        self,
        relevant_contents: List[tuple]
    ) -> List[AgentResult]:
        """顺序处理"""
        results = []

        for agent_type, content in relevant_contents:
            if agent_type in self.agents:
                try:
                    result = await self.agents[agent_type].process_with_fallback(content)
                    results.append(result)
                    self.logger.debug(f"Agent {agent_type} completed successfully")
                except Exception as e:
                    self.logger.error(f"Agent {agent_type} failed: {e}")
                    failed_result = AgentResult(
                        result_id=f"failed_{len(results)}",
                        agent_type=agent_type,
                        status=AgentStatus.FAILED,
                        error_message=str(e)
                    )
                    results.append(failed_result)

        return results

    async def _integrate_results(
        self,
        agent_results: List[AgentResult],
        coordination_id: str
    ) -> Dict[str, Any]:
        """整合结果"""
        self.logger.info(f"Integrating {len(agent_results)} agent results")

        # 基本统计
        successful_results = [r for r in agent_results if r.status == AgentStatus.COMPLETED]
        failed_results = [r for r in agent_results if r.status == AgentStatus.FAILED]

        # 提取关键信息
        all_findings = []
        all_recommendations = []
        all_summaries = []

        for result in successful_results:
            all_findings.extend(result.key_findings)
            all_recommendations.extend(result.recommendations)
            all_summaries.append(result.summary)

        # 计算整体置信度
        overall_confidence = 0.0
        if successful_results:
            overall_confidence = sum(r.confidence_score for r in successful_results) / len(successful_results)

        # 检测冲突意见
        conflicts = await self._detect_conflicts(successful_results)

        integrated_result = {
            "coordination_id": coordination_id,
            "successful_agents": len(successful_results),
            "failed_agents": len(failed_results),
            "overall_confidence": overall_confidence,
            "findings": all_findings[:20],  # 限制数量
            "recommendations": all_recommendations[:20],
            "agent_summaries": all_summaries,
            "conflicts": conflicts,
            "integration_timestamp": datetime.utcnow().isoformat()
        }

        return integrated_result

    async def _assess_quality(self, integrated_result: Dict[str, Any]) -> Dict[str, Any]:
        """评估质量"""
        quality_metrics = {
            "overall_score": 0.0,
            "completeness": 0.0,
            "consistency": 0.0,
            "confidence": integrated_result.get("overall_confidence", 0.0)
        }

        # 完整性评分
        successful_agents = integrated_result.get("successful_agents", 0)
        total_possible_agents = 5  # 总共5种智能体类型
        quality_metrics["completeness"] = successful_agents / total_possible_agents

        # 一致性评分
        conflicts = integrated_result.get("conflicts", [])
        if not conflicts:
            quality_metrics["consistency"] = 1.0
        else:
            quality_metrics["consistency"] = max(0.0, 1.0 - len(conflicts) * 0.1)

        # 总体评分
        quality_metrics["overall_score"] = (
            quality_metrics["completeness"] * 0.4 +
            quality_metrics["consistency"] * 0.3 +
            quality_metrics["confidence"] * 0.3
        )

        return quality_metrics

    async def _detect_conflicts(self, agent_results: List[AgentResult]) -> List[Dict[str, Any]]:
        """检测冲突意见"""
        conflicts = []

        if len(agent_results) < 2:
            return conflicts

        # 简单的冲突检测：检查置信度差异
        confidence_scores = [r.confidence_score for r in agent_results if r.confidence_score]
        if confidence_scores:
            max_confidence = max(confidence_scores)
            min_confidence = min(confidence_scores)

            if max_confidence - min_confidence > 0.5:
                conflicts.append({
                    "type": "confidence_discrepancy",
                    "description": f"Large confidence gap: {min_confidence:.2f} - {max_confidence:.2f}",
                    "severity": "medium"
                })

        # 检查建议冲突
        recommendations = []
        for result in agent_results:
            if hasattr(result, 'recommendations'):
                recommendations.extend(result.recommendations)

        # 如果有冲突的建议，标记为潜在冲突
        if len(recommendations) > 10:
            conflicts.append({
                "type": "recommendation_overload",
                "description": "Too many recommendations may indicate lack of focus",
                "severity": "low"
            })

        return conflicts

    def _calculate_relevance_score(self, agent_type: AgentType, content: str) -> float:
        """计算相关性评分"""
        content_lower = content.lower()

        relevance_keywords = {
            AgentType.DIAGNOSIS: ["diagnosis", "symptom", "sign", "finding", "诊断", "症状"],
            AgentType.TREATMENT: ["treatment", "therapy", "medication", "intervention", "治疗", "药物"],
            AgentType.PREVENTION: ["prevention", "prevention", "screening", "vaccine", "预防", "筛查"],
            AgentType.MONITORING: ["monitor", "follow-up", "track", "observe", "监测", "随访"],
            AgentType.SPECIAL_POPULATIONS: ["pediatric", "geriatric", "pregnant", "儿童", "老年", "孕妇"]
        }

        keywords = relevance_keywords.get(agent_type, [])
        if not keywords:
            return 0.5  # 默认相关性

        matches = sum(1 for keyword in keywords if keyword in content_lower)
        return min(1.0, matches / len(keywords) + 0.2)  # 基础分 + 匹配分

    def _get_agent_priority(self, agent_type: AgentType) -> int:
        """获取智能体优先级"""
        priorities = {
            AgentType.DIAGNOSIS: 10,  # 最高优先级
            AgentType.TREATMENT: 8,
            AgentType.MONITORING: 7,
            AgentType.PREVENTION: 6,
            AgentType.SPECIAL_POPULATIONS: 5
        }
        return priorities.get(agent_type, 5)

    def get_available_agents(self) -> List[Dict[str, Any]]:
        """获取可用智能体信息"""
        return [
            {
                "type": agent_type.value,
                "name": agent_type.value.title(),
                "available": True,
                "priority": self._get_agent_priority(agent_type)
            }
            for agent_type in AgentType
        ]

    async def get_orchestration_stats(self) -> Dict[str, Any]:
        """获取协调统计信息"""
        return {
            "available_agents": len(self.agents),
            "agent_types": [agent_type.value for agent_type in self.agents.keys()],
            "supported_strategies": [strategy.value for strategy in ProcessingStrategy],
            "capabilities": [
                "parallel_processing",
                "sequential_processing",
                "conflict_detection",
                "quality_assessment",
                "result_integration"
            ]
        }


# 全局实例
agent_orchestrator = AgentOrchestrator()


async def get_agent_orchestrator() -> AgentOrchestrator:
    """获取智能体协调器实例"""
    return agent_orchestrator


# 便捷函数
async def orchestrate_medical_analysis(
    content: str,
    strategy: ProcessingStrategy = ProcessingStrategy.PARALLEL,
    agent_types: Optional[List[AgentType]] = None
) -> Dict[str, Any]:
    """协调医学分析的便捷函数"""
    orchestrator = await get_agent_orchestrator()

    content_data = {
        "content": content,
        "content_id": str(uuid.uuid4())
    }

    return await orchestrator.orchestrate_processing(
        content_data=content_data,
        strategy=strategy,
        agent_types=agent_types
    )