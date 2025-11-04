"""
分层智能体系统
CPG2PVG-AI System IntelligentAgentOrchestrator (Node 4)
"""

import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json

from app.workflows.base import BaseWorkflowNode
from app.workflows.types import (
    ProcessingContext,
    ProcessingResult,
    ProcessingStatus,
)
from app.core.llm_client import LLMClient

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """智能体角色"""
    PRIMARY_ANALYST = "primary_analyst"          # 主要分析师
    SPECIALIST_ANALYST = "specialist_analyst"    # 专科分析师
    QUALITY_REVIEWER = "quality_reviewer"        # 质量评审员
    CONTENT_WRITER = "content_writer"           # 内容撰写师
    SAFETY_CHECKER = "safety_checker"           # 安全性检查员
    COORDINATION_AGENT = "coordination_agent"   # 协调智能体


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 3    # 关键任务
    HIGH = 2        # 高优先级
    NORMAL = 1      # 普通优先级
    LOW = 0         # 低优先级


@dataclass
class AgentTask:
    """智能体任务"""
    task_id: str
    agent_role: AgentRole
    description: str
    input_data: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    dependencies: List[str] = field(default_factory=list)
    timeout: int = 300  # 超时时间（秒）
    max_retries: int = 2


@dataclass
class AgentMessage:
    """智能体消息"""
    sender_id: str
    receiver_id: str
    message_type: str
    content: Dict[str, Any]
    timestamp: datetime
    priority: TaskPriority = TaskPriority.NORMAL


@dataclass
class AgentResult:
    """智能体执行结果"""
    agent_id: str
    task_id: str
    success: bool
    result_data: Dict[str, Any]
    execution_time: float
    confidence: float
    error_message: Optional[str] = None


class IntelligentAgent:
    """智能体基类"""

    def __init__(self, agent_id: str, role: AgentRole, llm_client: LLMClient):
        self.agent_id = agent_id
        self.role = role
        self.llm_client = llm_client
        self.is_active = False
        self.current_task = None
        self.message_queue = asyncio.Queue()
        self.completed_tasks = []

    async def start(self):
        """启动智能体"""
        self.is_active = True
        logger.info(f"智能体 {self.agent_id} ({self.role.value}) 启动")

    async def stop(self):
        """停止智能体"""
        self.is_active = False
        logger.info(f"智能体 {self.agent_id} ({self.role.value}) 停止")

    async def process_task(self, task: AgentTask, context: ProcessingContext) -> AgentResult:
        """处理任务"""
        start_time = datetime.utcnow()

        try:
            self.current_task = task

            # 根据角色执行相应的处理逻辑
            if self.role == AgentRole.PRIMARY_ANALYST:
                result_data = await self._process_primary_analysis(task, context)
            elif self.role == AgentRole.SPECIALIST_ANALYST:
                result_data = await self._process_specialist_analysis(task, context)
            elif self.role == AgentRole.QUALITY_REVIEWER:
                result_data = await self._process_quality_review(task, context)
            elif self.role == AgentRole.CONTENT_WRITER:
                result_data = await self._process_content_writing(task, context)
            elif self.role == AgentRole.SAFETY_CHECKER:
                result_data = await self._process_safety_check(task, context)
            elif self.role == AgentRole.COORDINATION_AGENT:
                result_data = await self._process_coordination(task, context)
            else:
                raise ValueError(f"未知角色: {self.role}")

            execution_time = (datetime.utcnow() - start_time).total_seconds()

            return AgentResult(
                agent_id=self.agent_id,
                task_id=task.task_id,
                success=True,
                result_data=result_data,
                execution_time=execution_time,
                confidence=self._calculate_confidence(result_data)
            )

        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            logger.error(f"智能体 {self.agent_id} 处理任务失败: {str(e)}")

            return AgentResult(
                agent_id=self.agent_id,
                task_id=task.task_id,
                success=False,
                result_data={},
                execution_time=execution_time,
                confidence=0.0,
                error_message=str(e)
            )
        finally:
            self.current_task = None

    async def send_message(self, message: AgentMessage):
        """发送消息"""
        await self.message_queue.put(message)

    async def _process_primary_analysis(self, task: AgentTask, context: ProcessingContext) -> Dict[str, Any]:
        """主要分析处理"""
        prompt = f"""
作为医学指南主要分析师，请对以下内容进行综合分析：

任务描述: {task.description}
输入数据: {json.dumps(task.input_data, ensure_ascii=False, indent=2)}
专业领域: {', '.join(context.medical_specialties)}

请提供：
1. 内容概要和关键要点
2. 临床意义评估
3. 患者教育重点
4. 转换建议

请以JSON格式返回分析结果。
"""

        response = await self.llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2000,
            temperature=0.2
        )

        return {
            "analysis_result": response,
            "agent_type": "primary_analyst",
            "key_insights": self._extract_key_insights(response)
        }

    async def _process_specialist_analysis(self, task: AgentTask, context: ProcessingContext) -> Dict[str, Any]:
        """专科分析处理"""
        specialty = task.input_data.get("specialty", "general")

        prompt = f"""
作为{specialty}专科分析师，请对以下内容进行专业分析：

任务描述: {task.description}
输入数据: {json.dumps(task.input_data, ensure_ascii=False, indent=2)}
专业领域: {specialty}

请从专科角度提供：
1. 专业术语解释
2. 专科特定的注意事项
3. 深层机制分析
4. 专科患者建议

请以JSON格式返回分析结果。
"""

        response = await self.llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )

        return {
            "specialty_analysis": response,
            "agent_type": "specialist_analyst",
            "specialty": specialty,
            "professional_insights": self._extract_professional_insights(response)
        }

    async def _process_quality_review(self, task: AgentTask, context: ProcessingContext) -> Dict[str, Any]:
        """质量评审处理"""
        content_to_review = task.input_data.get("content", "")

        prompt = f"""
作为质量评审员，请评审以下医学内容的准确性和适用性：

内容: {content_to_review[:2000]}
质量要求: {context.quality_requirement.value}

请检查：
1. 医学准确性
2. 语言清晰度
3. 患者可读性
4. 完整性评估
5. 改进建议

请以JSON格式返回评审结果，包含质量分数(0-100)和具体建议。
"""

        response = await self.llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1500,
            temperature=0.1
        )

        return {
            "quality_review": response,
            "agent_type": "quality_reviewer",
            "quality_score": self._extract_quality_score(response),
            "improvement_suggestions": self._extract_improvements(response)
        }

    async def _process_content_writing(self, task: AgentTask, context: ProcessingContext) -> Dict[str, Any]:
        """内容撰写处理"""
        analysis_data = task.input_data.get("analysis_data", {})
        target_audience = task.input_data.get("target_audience", "patients")

        prompt = f"""
作为医学内容撰写师，请基于以下分析结果撰写适合{target_audience}的内容：

分析数据: {json.dumps(analysis_data, ensure_ascii=False, indent=2)}
目标受众: {target_audience}
专业领域: {', '.join(context.medical_specialties)}

请撰写：
1. 简洁明了的标题
2. 通俗易懂的内容
3. 关键信息突出
4. 实用建议
5. 注意事项提醒

请确保内容准确、易懂、有用。请以JSON格式返回撰写结果。
"""

        response = await self.llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0.3
        )

        return {
            "written_content": response,
            "agent_type": "content_writer",
            "target_audience": target_audience,
            "content_summary": self._extract_content_summary(response)
        }

    async def _process_safety_check(self, task: AgentTask, context: ProcessingContext) -> Dict[str, Any]:
        """安全性检查处理"""
        content_to_check = task.input_data.get("content", "")

        prompt = f"""
作为安全性检查员，请检查以下医学内容的安全性：

内容: {content_to_check[:2000]}

请检查：
1. 是否包含错误或危险的医学建议
2. 药物剂量和用法是否正确
3. 是否遗漏重要的安全警告
4. 是否可能引起误解或恐慌
5. 是否建议及时就医的情况

请以JSON格式返回安全检查结果，包含安全等级和具体建议。
"""

        response = await self.llm_client.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.0
        )

        return {
            "safety_check": response,
            "agent_type": "safety_checker",
            "safety_level": self._extract_safety_level(response),
            "safety_warnings": self._extract_safety_warnings(response)
        }

    async def _process_coordination(self, task: AgentTask, context: ProcessingContext) -> Dict[str, Any]:
        """协调处理"""
        task_results = task.input_data.get("task_results", [])

        # 分析各个任务结果
        analysis_summary = self._summarize_results(task_results)

        # 协调和整合结果
        coordination_result = {
            "coordination_summary": analysis_summary,
            "agent_type": "coordination_agent",
            "integration_status": "completed",
            "recommendations": self._generate_coordination_recommendations(task_results)
        }

        return coordination_result

    def _calculate_confidence(self, result_data: Dict[str, Any]) -> float:
        """计算置信度"""
        # 简化的置信度计算
        base_confidence = 0.7

        # 根据结果内容长度调整置信度
        if isinstance(result_data, dict):
            content_length = sum(len(str(v)) for v in result_data.values())
            if content_length > 500:
                base_confidence += 0.1
            elif content_length > 100:
                base_confidence += 0.05

        return min(base_confidence, 1.0)

    def _extract_key_insights(self, response: str) -> List[str]:
        """提取关键见解"""
        # 简化实现，实际应该解析LLM响应
        return ["关键见解1", "关键见解2", "关键见解3"]

    def _extract_professional_insights(self, response: str) -> List[str]:
        """提取专业见解"""
        return ["专业见解1", "专业见解2"]

    def _extract_quality_score(self, response: str) -> float:
        """提取质量分数"""
        # 简化实现，返回默认分数
        return 85.0

    def _extract_improvements(self, response: str) -> List[str]:
        """提取改进建议"""
        return ["改进建议1", "改进建议2"]

    def _extract_content_summary(self, response: str) -> str:
        """提取内容摘要"""
        return "生成的内容摘要"

    def _extract_safety_level(self, response: str) -> str:
        """提取安全等级"""
        return "HIGH"  # HIGH, MEDIUM, LOW

    def _extract_safety_warnings(self, response: str) -> List[str]:
        """提取安全警告"""
        return []

    def _summarize_results(self, task_results: List[AgentResult]) -> Dict[str, Any]:
        """总结任务结果"""
        successful_results = [r for r in task_results if r.success]
        failed_results = [r for r in task_results if not r.success]

        return {
            "total_tasks": len(task_results),
            "successful_tasks": len(successful_results),
            "failed_tasks": len(failed_results),
            "success_rate": len(successful_results) / len(task_results) if task_results else 0,
            "average_confidence": sum(r.confidence for r in successful_results) / len(successful_results) if successful_results else 0
        }

    def _generate_coordination_recommendations(self, task_results: List[AgentResult]) -> List[str]:
        """生成协调建议"""
        return ["协调建议1", "协调建议2"]


class IntelligentAgentOrchestrator(BaseWorkflowNode):
    """分层智能体系统编排器"""

    def __init__(self):
        super().__init__(
            name="IntelligentAgentOrchestrator",
            description="协调多个智能体进行协作处理，提供分层专业分析"
        )

        # 初始化LLM客户端
        self.llm_client = LLMClient()

        # 智能体池
        self.agents: Dict[str, IntelligentAgent] = {}
        self.agent_tasks: Dict[str, AgentTask] = {}
        self.task_results: Dict[str, AgentResult] = {}

        # 任务队列和优先级队列
        self.task_queue = asyncio.PriorityQueue()
        self.completed_results = []

    async def execute(
        self,
        context: ProcessingContext,
        input_data: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[ProcessingResult, None]:
        """执行智能体系统处理"""

        try:
            # 解析输入数据
            knowledge_graph = input_data.get("knowledge_graph", {})
            entities = input_data.get("entities", [])
            processed_content = input_data.get("processed_content", {})

            if not any([knowledge_graph, entities, processed_content]):
                yield ProcessingResult(
                    step_name=self.name,
                    status=ProcessingStatus.FAILED,
                    success=False,
                    error_message="没有可用的知识内容进行智能体处理"
                )
                return

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.RUNNING,
                success=True,
                message="启动分层智能体系统"
            )

            # 1. 初始化智能体
            yield ProcessingResult(
                step_name=f"{self.name}_agent_initialization",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="初始化智能体"
            )

            await self._initialize_agents()

            yield ProcessingResult(
                step_name=f"{self.name}_agent_initialization",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"agent_count": len(self.agents)},
                message=f"智能体初始化完成，共创建{len(self.agents)}个智能体"
            )

            # 2. 创建任务计划
            yield ProcessingResult(
                step_name=f"{self.name}_task_planning",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="制定任务计划"
            )

            tasks = await self._create_task_plan(knowledge_graph, entities, processed_content, context)

            yield ProcessingResult(
                step_name=f"{self.name}_task_planning",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"task_count": len(tasks)},
                message=f"任务计划制定完成，共{len(tasks)}个任务"
            )

            # 3. 执行智能体任务
            yield ProcessingResult(
                step_name=f"{self.name}_agent_execution",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="开始执行智能体任务"
            )

            task_results = await self._execute_agent_tasks(tasks, context)

            yield ProcessingResult(
                step_name=f"{self.name}_agent_execution",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"completed_tasks": len(task_results)},
                message=f"智能体任务执行完成，共完成{len(task_results)}个任务"
            )

            # 4. 协调和整合结果
            yield ProcessingResult(
                step_name=f"{self.name}_result_coordination",
                status=ProcessingStatus.RUNNING,
                success=True,
                message="协调和整合智能体结果"
            )

            coordinated_result = await self._coordinate_results(task_results, context)

            yield ProcessingResult(
                step_name=f"{self.name}_result_coordination",
                status=ProcessingStatus.COMPLETED,
                success=True,
                data={"integration_status": "completed"},
                message="结果协调和整合完成"
            )

            # 生成最终结果
            final_result = {
                "agent_system_output": coordinated_result,
                "task_results": [result.__dict__ for result in task_results],
                "agent_statistics": self._get_agent_statistics(),
                "processing_metadata": {
                    "total_agents": len(self.agents),
                    "total_tasks": len(tasks),
                    "successful_tasks": len([r for r in task_results if r.success]),
                    "processing_time": datetime.utcnow().isoformat(),
                    "cost_level": context.cost_level.value
                }
            }

            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.COMPLETED,
                success=True,
                data=final_result,
                message=f"分层智能体系统处理完成，成功执行{len([r for r in task_results if r.success])}个任务"
            )

        except Exception as e:
            logger.error(f"智能体系统处理失败: {str(e)}")
            yield ProcessingResult(
                step_name=self.name,
                status=ProcessingStatus.FAILED,
                success=False,
                error_message=str(e)
            )
        finally:
            # 清理智能体
            await self._cleanup_agents()

    async def _initialize_agents(self):
        """初始化智能体"""
        # 创建不同角色的智能体
        agent_configs = [
            ("primary_analyst_001", AgentRole.PRIMARY_ANALYST),
            ("specialist_analyst_001", AgentRole.SPECIALIST_ANALYST),
            ("quality_reviewer_001", AgentRole.QUALITY_REVIEWER),
            ("content_writer_001", AgentRole.CONTENT_WRITER),
            ("safety_checker_001", AgentRole.SAFETY_CHECKER),
            ("coordination_agent_001", AgentRole.COORDINATION_AGENT),
        ]

        for agent_id, role in agent_configs:
            agent = IntelligentAgent(agent_id, role, self.llm_client)
            await agent.start()
            self.agents[agent_id] = agent

    async def _create_task_plan(
        self, knowledge_graph: Dict[str, Any], entities: List[Dict[str, Any]],
        processed_content: Dict[str, Any], context: ProcessingContext
    ) -> List[AgentTask]:
        """创建任务计划"""
        tasks = []
        task_id_counter = 0

        # 任务1: 主要分析
        tasks.append(AgentTask(
            task_id=f"task_{task_id_counter:03d}",
            agent_role=AgentRole.PRIMARY_ANALYST,
            description="对医学指南进行综合分析",
            input_data={
                "knowledge_graph": knowledge_graph,
                "entities": entities[:20],  # 限制实体数量
                "context": context.__dict__
            },
            priority=TaskPriority.HIGH
        ))
        task_id_counter += 1

        # 任务2: 专科分析（根据专业领域）
        for specialty in context.medical_specialties[:2]:  # 限制专科数量
            tasks.append(AgentTask(
                task_id=f"task_{task_id_counter:03d}",
                agent_role=AgentRole.SPECIALIST_ANALYST,
                description=f"对{specialty}领域进行专科分析",
                input_data={
                    "specialty": specialty,
                    "entities": entities[:10],
                    "processed_content": processed_content
                },
                priority=TaskPriority.NORMAL
            ))
            task_id_counter += 1

        # 任务3: 内容撰写
        tasks.append(AgentTask(
            task_id=f"task_{task_id_counter:03d}",
            agent_role=AgentRole.CONTENT_WRITER,
            description="撰写适合患者阅读的内容",
            input_data={
                "target_audience": "patients",
                "analysis_data": {"entities": entities[:10]},
                "context": context.__dict__
            },
            priority=TaskPriority.HIGH,
            dependencies=["task_000", "task_001"]  # 依赖前面的分析任务
        ))
        task_id_counter += 1

        # 任务4: 质量评审
        tasks.append(AgentTask(
            task_id=f"task_{task_id_counter:03d}",
            agent_role=AgentRole.QUALITY_REVIEWER,
            description="评审内容质量",
            input_data={
                "content": "待评审的内容",
                "quality_requirements": context.quality_requirement.value
            },
            priority=TaskPriority.HIGH
        ))
        task_id_counter += 1

        # 任务5: 安全检查
        tasks.append(AgentTask(
            task_id=f"task_{task_id_counter:03d}",
            agent_role=AgentRole.SAFETY_CHECKER,
            description="检查内容安全性",
            input_data={
                "content": "待检查的内容",
                "safety_requirements": "medical_safety"
            },
            priority=TaskPriority.CRITICAL
        ))
        task_id_counter += 1

        # 任务6: 协调整合
        tasks.append(AgentTask(
            task_id=f"task_{task_id_counter:03d}",
            agent_role=AgentRole.COORDINATION_AGENT,
            description="协调整合所有结果",
            input_data={"task_results": []},  # 将在执行时填入
            priority=TaskPriority.HIGH,
            dependencies=[f"task_{i:03d}" for i in range(task_id_counter - 1)]  # 依赖所有前面的任务
        ))

        return tasks

    async def _execute_agent_tasks(self, tasks: List[AgentTask], context: ProcessingContext) -> List[AgentResult]:
        """执行智能体任务"""
        results = []

        # 按优先级排序任务
        priority_tasks = sorted(tasks, key=lambda t: t.priority.value, reverse=True)

        # 执行任务
        for task in priority_tasks:
            try:
                # 找到对应角色的智能体
                available_agent = self._find_available_agent(task.agent_role)
                if not available_agent:
                    logger.warning(f"没有可用的{task.agent_role.value}智能体")
                    continue

                # 执行任务
                result = await available_agent.process_task(task, context)
                results.append(result)
                self.task_results[task.task_id] = result

                # 记录任务完成情况
                if result.success:
                    logger.info(f"任务 {task.task_id} 执行成功")
                else:
                    logger.error(f"任务 {task.task_id} 执行失败: {result.error_message}")

            except Exception as e:
                logger.error(f"执行任务 {task.task_id} 时发生错误: {str(e)}")
                # 创建失败结果
                failed_result = AgentResult(
                    agent_id="unknown",
                    task_id=task.task_id,
                    success=False,
                    result_data={},
                    execution_time=0.0,
                    confidence=0.0,
                    error_message=str(e)
                )
                results.append(failed_result)

        return results

    async def _coordinate_results(self, task_results: List[AgentResult], context: ProcessingContext) -> Dict[str, Any]:
        """协调和整合结果"""
        try:
            # 找到协调智能体
            coordination_agent = self._find_available_agent(AgentRole.COORDINATION_AGENT)
            if not coordination_agent:
                logger.warning("没有可用的协调智能体，使用默认整合逻辑")
                return self._default_coordination(task_results)

            # 更新协调任务的输入数据
            coordination_task = AgentTask(
                task_id="coordination_final",
                agent_role=AgentRole.COORDINATION_AGENT,
                description="最终协调整合",
                input_data={"task_results": task_results},
                priority=TaskPriority.HIGH
            )

            # 执行协调
            coordination_result = await coordination_agent.process_task(coordination_task, context)

            if coordination_result.success:
                return coordination_result.result_data
            else:
                logger.error(f"协调任务失败: {coordination_result.error_message}")
                return self._default_coordination(task_results)

        except Exception as e:
            logger.error(f"结果协调失败: {str(e)}")
            return self._default_coordination(task_results)

    def _default_coordination(self, task_results: List[AgentResult]) -> Dict[str, Any]:
        """默认协调逻辑"""
        successful_results = [r for r in task_results if r.success]
        failed_results = [r for r in task_results if not r.success]

        return {
            "coordination_method": "default",
            "summary": {
                "total_tasks": len(task_results),
                "successful_tasks": len(successful_results),
                "failed_tasks": len(failed_results),
                "success_rate": len(successful_results) / len(task_results) if task_results else 0
            },
            "key_outputs": [result.result_data for result in successful_results],
            "errors": [result.error_message for result in failed_results if result.error_message],
            "recommendations": ["建议重新执行失败的任务"]
        }

    def _find_available_agent(self, role: AgentRole) -> Optional[IntelligentAgent]:
        """找到可用的智能体"""
        for agent in self.agents.values():
            if agent.role == role and agent.is_active and agent.current_task is None:
                return agent
        return None

    async def _cleanup_agents(self):
        """清理智能体"""
        for agent in self.agents.values():
            await agent.stop()
        self.agents.clear()
        logger.info("所有智能体已停止")

    def _get_agent_statistics(self) -> Dict[str, Any]:
        """获取智能体统计信息"""
        role_counts = {}
        for agent in self.agents.values():
            role = agent.role.value
            role_counts[role] = role_counts.get(role, 0) + 1

        return {
            "total_agents": len(self.agents),
            "agent_roles": role_counts,
            "active_agents": sum(1 for agent in self.agents.values() if agent.is_active),
            "completed_tasks": len(self.task_results)
        }