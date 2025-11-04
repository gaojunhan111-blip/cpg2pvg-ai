"""
医学指南可视化器
Medical Guideline Visualizer
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import uuid
from datetime import datetime

from app.core.logger import get_logger
from app.core.error_handling import CPG2PVGException, retry, DEFAULT_RETRY_CONFIG

logger = get_logger(__name__)


class VisualizationType(str, Enum):
    """可视化类型"""
    WORKFLOW_FLOWCHART = "workflow_flowchart"
    EVIDENCE_NETWORK = "evidence_network"
    RECOMMENDATION_MATRIX = "recommendation_matrix"
    TIMELINE = "timeline"
    STATISTICS = "statistics"
    COMPARISON = "comparison"


class ChartType(str, Enum):
    """图表类型"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    NETWORK = "network"
    TREE = "tree"
    SANKEY = "sankey"


@dataclass
class ChartData:
    """图表数据"""
    chart_id: str
    chart_type: ChartType
    title: str
    data: Dict[str, Any]
    config: Dict[str, Any]
    metadata: Dict[str, Any]


@dataclass
class VisualizationResult:
    """可视化结果"""
    id: str
    viz_type: VisualizationType
    title: str
    description: str
    charts: List[ChartData]
    layout: Dict[str, Any]
    created_at: datetime
    metadata: Dict[str, Any]


class WorkflowVisualizer:
    """工作流可视化器"""

    def __init__(self):
        self.node_colors = {
            "preprocessing": "#E3F2FD",      # 浅蓝色
            "analysis": "#F3E5F5",          # 浅紫色
            "recommendation": "#E8F5E8",    # 浅绿色
            "visualization": "#FFF3E0",     # 浅橙色
            "quality_control": "#FFEBEE"    # 浅红色
        }

    @retry(config=DEFAULT_RETRY_CONFIG)
    async def create_workflow_flowchart(self, workflow_data: Dict[str, Any]) -> VisualizationResult:
        """创建工作流流程图"""
        try:
            logger.info("开始创建工作流流程图", extra_data={"workflow_id": workflow_data.get("id")})

            nodes = workflow_data.get("nodes", [])
            edges = workflow_data.get("edges", [])

            # 处理节点数据
            chart_nodes = []
            for i, node in enumerate(nodes):
                node_data = {
                    "id": node.get("id", f"node_{i}"),
                    "name": node.get("name", f"Node {i+1}"),
                    "type": node.get("type", "processing"),
                    "status": node.get("status", "pending"),
                    "position": {
                        "x": node.get("x", i * 200),
                        "y": node.get("y", 100)
                    },
                    "style": {
                        "fill": self._get_node_color(node.get("type", "processing")),
                        "stroke": "#333",
                        "strokeWidth": 2
                    },
                    "metadata": node.get("metadata", {})
                }
                chart_nodes.append(node_data)

            # 处理边数据
            chart_edges = []
            for edge in edges:
                edge_data = {
                    "id": f"edge_{edge.get('source', 'unknown')}_to_{edge.get('target', 'unknown')}",
                    "source": edge.get("source"),
                    "target": edge.get("target"),
                    "type": edge.get("type", "default"),
                    "style": {
                        "stroke": "#666",
                        "strokeWidth": 2,
                        "markerEnd": "arrow"
                    }
                }
                chart_edges.append(edge_data)

            # 创建流程图数据
            flowchart_data = {
                "nodes": chart_nodes,
                "edges": chart_edges,
                "layout": {
                    "type": "horizontal",
                    "nodeSpacing": 150,
                    "levelSpacing": 200
                }
            }

            chart = ChartData(
                chart_id=f"workflow_flowchart_{uuid.uuid4().hex[:8]}",
                chart_type=ChartType.NETWORK,
                title="工作流执行流程图",
                data=flowchart_data,
                config={
                    "width": 1200,
                    "height": 600,
                    "nodeSize": 80,
                    "labelPosition": "bottom",
                    "showProgress": True,
                    "animateTransitions": True
                },
                metadata={
                    "node_count": len(nodes),
                    "edge_count": len(edges),
                    "created_at": datetime.utcnow().isoformat()
                }
            )

            result = VisualizationResult(
                id=f"viz_{uuid.uuid4().hex[:8]}",
                viz_type=VisualizationType.WORKFLOW_FLOWCHART,
                title="工作流可视化",
                description="展示工作流执行过程和节点状态",
                charts=[chart],
                layout={
                    "type": "single",
                    "spacing": "normal"
                },
                created_at=datetime.utcnow(),
                metadata={
                    "workflow_id": workflow_data.get("id"),
                    "total_nodes": len(nodes),
                    "completed_nodes": len([n for n in nodes if n.get("status") == "completed"])
                }
            )

            logger.info("工作流流程图创建成功", extra_data={
                "result_id": result.id,
                "node_count": len(nodes)
            })

            return result

        except Exception as e:
            logger.error("创建工作流流程图失败", extra_data={"error": str(e)})
            raise CPG2PVGException(
                message=f"工作流可视化失败: {str(e)}",
                category="business_logic",
                severity="medium",
                details={"error": str(e)}
            )

    def _get_node_color(self, node_type: str) -> str:
        """获取节点颜色"""
        return self.node_colors.get(node_type, "#F5F5F5")


class EvidenceVisualizer:
    """证据可视化器"""

    @retry(config=DEFAULT_RETRY_CONFIG)
    async def create_evidence_network(self, evidence_data: Dict[str, Any]) -> VisualizationResult:
        """创建证据网络图"""
        try:
            logger.info("开始创建证据网络图", extra_data={"evidence_count": len(evidence_data.get("evidences", []))})

            evidences = evidence_data.get("evidences", [])
            relationships = evidence_data.get("relationships", [])

            # 构建证据节点
            nodes = []
            for i, evidence in enumerate(evidences):
                node = {
                    "id": evidence.get("id", f"evidence_{i}"),
                    "name": evidence.get("title", f"Evidence {i+1}"),
                    "type": "evidence",
                    "size": max(20, min(60, evidence.get("weight", 1) * 40)),
                    "color": self._get_evidence_color(evidence.get("level", "B")),
                    "metadata": {
                        "level": evidence.get("level"),
                        "quality": evidence.get("quality"),
                        "source": evidence.get("source")
                    }
                }
                nodes.append(node)

            # 构建关系边
            edges = []
            for rel in relationships:
                edge = {
                    "source": rel.get("source"),
                    "target": rel.get("target"),
                    "weight": rel.get("weight", 1),
                    "type": rel.get("type", "supports"),
                    "color": self._get_relationship_color(rel.get("type", "supports"))
                }
                edges.append(edge)

            network_data = {
                "nodes": nodes,
                "edges": edges,
                "layout": {
                    "type": "force",
                    "iterations": 100,
                    "nodeSpacing": 100,
                    "edgeLength": 150
                }
            }

            chart = ChartData(
                chart_id=f"evidence_network_{uuid.uuid4().hex[:8]}",
                chart_type=ChartType.NETWORK,
                title="证据关系网络图",
                data=network_data,
                config={
                    "width": 1000,
                    "height": 700,
                    "nodeLabels": True,
                    "edgeLabels": False,
                    "enableDrag": True,
                    "enableZoom": True
                },
                metadata={
                    "node_count": len(nodes),
                    "edge_count": len(edges)
                }
            )

            # 创建证据级别统计图
            level_stats = self._calculate_evidence_level_stats(evidences)
            pie_chart = ChartData(
                chart_id=f"evidence_level_pie_{uuid.uuid4().hex[:8]}",
                chart_type=ChartType.PIE,
                title="证据级别分布",
                data=level_stats,
                config={
                    "width": 400,
                    "height": 300,
                    "showLegend": True,
                    "showPercentage": True
                },
                metadata={}
            )

            result = VisualizationResult(
                id=f"viz_{uuid.uuid4().hex[:8]}",
                viz_type=VisualizationType.EVIDENCE_NETWORK,
                title="证据可视化",
                description="展示医学证据之间的关系和分布",
                charts=[chart, pie_chart],
                layout={
                    "type": "grid",
                    "columns": 2,
                    "spacing": "normal"
                },
                created_at=datetime.utcnow(),
                metadata={
                    "total_evidences": len(evidences),
                    "total_relationships": len(relationships)
                }
            )

            logger.info("证据网络图创建成功", extra_data={
                "result_id": result.id,
                "evidence_count": len(evidences)
            })

            return result

        except Exception as e:
            logger.error("创建证据网络图失败", extra_data={"error": str(e)})
            raise CPG2PVGException(
                message=f"证据可视化失败: {str(e)}",
                category="business_logic",
                severity="medium"
            )

    def _get_evidence_color(self, level: str) -> str:
        """根据证据级别获取颜色"""
        level_colors = {
            "A": "#4CAF50",  # 绿色 - 高质量
            "B": "#2196F3",  # 蓝色 - 中等质量
            "C": "#FF9800",  # 橙色 - 低质量
            "D": "#F44336"   # 红色 - 很低质量
        }
        return level_colors.get(level, "#9E9E9E")

    def _get_relationship_color(self, rel_type: str) -> str:
        """根据关系类型获取颜色"""
        rel_colors = {
            "supports": "#4CAF50",    # 绿色 - 支持
            "contradicts": "#F44336", # 红色 - 矛盾
            "related": "#2196F3",     # 蓝色 - 相关
            "refutes": "#FF9800"      # 橙色 - 反驳
        }
        return rel_colors.get(rel_type, "#9E9E9E")

    def _calculate_evidence_level_stats(self, evidences: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算证据级别统计"""
        level_counts = {}
        for evidence in evidences:
            level = evidence.get("level", "Unknown")
            level_counts[level] = level_counts.get(level, 0) + 1

        return {
            "labels": list(level_counts.keys()),
            "datasets": [{
                "data": list(level_counts.values()),
                "backgroundColor": [self._get_evidence_color(level) for level in level_counts.keys()]
            }]
        }


class RecommendationVisualizer:
    """推荐意见可视化器"""

    @retry(config=DEFAULT_RETRY_CONFIG)
    async def create_recommendation_matrix(self, recommendation_data: Dict[str, Any]) -> VisualizationResult:
        """创建推荐意见矩阵图"""
        try:
            logger.info("开始创建推荐意见矩阵图",
                       extra_data={"recommendation_count": len(recommendation_data.get("recommendations", []))})

            recommendations = recommendation_data.get("recommendations", [])

            # 构建矩阵数据
            matrix_data = []
            categories = []
            strength_levels = ["Strong", "Moderate", "Weak", "Consensus"]

            for i, rec in enumerate(recommendations):
                category = rec.get("category", f"Category {i+1}")
                if category not in categories:
                    categories.append(category)

                strength = rec.get("strength", "Moderate")
                row = {
                    "x": categories.index(category),
                    "y": strength_levels.index(strength),
                    "value": 1,
                    "recommendation": rec.get("text", ""),
                    "evidence_level": rec.get("evidence_level", "B")
                }
                matrix_data.append(row)

            # 热力图数据
            heatmap_data = {
                "xAxis": categories,
                "yAxis": strength_levels,
                "data": matrix_data,
                "colorScale": [
                    [0, "#E3F2FD"],
                    [0.25, "#90CAF9"],
                    [0.5, "#42A5F5"],
                    [0.75, "#1E88E5"],
                    [1, "#1565C0"]
                ]
            }

            heatmap_chart = ChartData(
                chart_id=f"recommendation_heatmap_{uuid.uuid4().hex[:8]}",
                chart_type=ChartType.SCATTER,
                title="推荐意见强度矩阵",
                data=heatmap_data,
                config={
                    "width": 800,
                    "height": 500,
                    "showTooltip": True,
                    "colorScale": "blues"
                },
                metadata={
                    "recommendation_count": len(recommendations),
                    "categories": len(categories)
                }
            )

            # 推荐意见统计柱状图
            category_stats = {}
            for rec in recommendations:
                category = rec.get("category", "Unknown")
                category_stats[category] = category_stats.get(category, 0) + 1

            bar_data = {
                "labels": list(category_stats.keys()),
                "datasets": [{
                    "label": "推荐意见数量",
                    "data": list(category_stats.values()),
                    "backgroundColor": "#2196F3",
                    "borderColor": "#1976D2",
                    "borderWidth": 1
                }]
            }

            bar_chart = ChartData(
                chart_id=f"recommendation_bar_{uuid.uuid4().hex[:8]}",
                chart_type=ChartType.BAR,
                title="各类别推荐意见数量分布",
                data=bar_data,
                config={
                    "width": 600,
                    "height": 400,
                    "showLegend": False,
                    "rotateLabels": 45
                },
                metadata={}
            )

            result = VisualizationResult(
                id=f"viz_{uuid.uuid4().hex[:8]}",
                viz_type=VisualizationType.RECOMMENDATION_MATRIX,
                title="推荐意见可视化",
                description="展示推荐意见的强度分布和分类统计",
                charts=[heatmap_chart, bar_chart],
                layout={
                    "type": "vertical",
                    "spacing": "large"
                },
                created_at=datetime.utcnow(),
                metadata={
                    "total_recommendations": len(recommendations),
                    "categories": len(categories)
                }
            )

            logger.info("推荐意见矩阵图创建成功", extra_data={
                "result_id": result.id,
                "recommendation_count": len(recommendations)
            })

            return result

        except Exception as e:
            logger.error("创建推荐意见矩阵图失败", extra_data={"error": str(e)})
            raise CPG2PVGException(
                message=f"推荐意见可视化失败: {str(e)}",
                category="business_logic",
                severity="medium"
            )


class StatisticsVisualizer:
    """统计可视化器"""

    @retry(config=DEFAULT_RETRY_CONFIG)
    async def create_statistics_dashboard(self, stats_data: Dict[str, Any]) -> VisualizationResult:
        """创建统计仪表板"""
        try:
            logger.info("开始创建统计仪表板")

            charts = []

            # 处理时间统计
            if "processing_times" in stats_data:
                time_data = stats_data["processing_times"]
                line_chart = ChartData(
                    chart_id=f"processing_time_line_{uuid.uuid4().hex[:8]}",
                    chart_type=ChartType.LINE,
                    title="处理时间趋势",
                    data={
                        "labels": time_data.get("timestamps", []),
                        "datasets": [{
                            "label": "处理时间 (秒)",
                            "data": time_data.get("values", []),
                            "borderColor": "#2196F3",
                            "backgroundColor": "rgba(33, 150, 243, 0.1)",
                            "fill": True
                        }]
                    },
                    config={
                        "width": 800,
                        "height": 300,
                        "showGrid": True,
                        "showLegend": True
                    },
                    metadata={}
                )
                charts.append(line_chart)

            # 处理成功率统计
            if "success_rates" in stats_data:
                success_data = stats_data["success_rates"]
                pie_chart = ChartData(
                    chart_id=f"success_rate_pie_{uuid.uuid4().hex[:8]}",
                    chart_type=ChartType.PIE,
                    title="任务成功率统计",
                    data={
                        "labels": ["成功", "失败", "进行中"],
                        "datasets": [{
                            "data": [
                                success_data.get("successful", 0),
                                success_data.get("failed", 0),
                                success_data.get("pending", 0)
                            ],
                            "backgroundColor": ["#4CAF50", "#F44336", "#FF9800"]
                        }]
                    },
                    config={
                        "width": 400,
                        "height": 300,
                        "showPercentage": True
                    },
                    metadata={}
                )
                charts.append(pie_chart)

            # 处理文档类型统计
            if "document_types" in stats_data:
                doc_data = stats_data["document_types"]
                bar_chart = ChartData(
                    chart_id=f"doc_type_bar_{uuid.uuid4().hex[:8]}",
                    chart_type=ChartType.BAR,
                    title="文档类型分布",
                    data={
                        "labels": list(doc_data.keys()),
                        "datasets": [{
                            "label": "文档数量",
                            "data": list(doc_data.values()),
                            "backgroundColor": "#9C27B0",
                            "borderColor": "#7B1FA2"
                        }]
                    },
                    config={
                        "width": 600,
                        "height": 400,
                        "rotateLabels": 45
                    },
                    metadata={}
                )
                charts.append(bar_chart)

            result = VisualizationResult(
                id=f"viz_{uuid.uuid4().hex[:8]}",
                viz_type=VisualizationType.STATISTICS,
                title="系统统计仪表板",
                description="展示系统运行的关键统计数据",
                charts=charts,
                layout={
                    "type": "grid",
                    "columns": 2,
                    "spacing": "normal"
                },
                created_at=datetime.utcnow(),
                metadata={
                    "chart_count": len(charts),
                    "data_timestamp": datetime.utcnow().isoformat()
                }
            )

            logger.info("统计仪表板创建成功", extra_data={
                "result_id": result.id,
                "chart_count": len(charts)
            })

            return result

        except Exception as e:
            logger.error("创建统计仪表板失败", extra_data={"error": str(e)})
            raise CPG2PVGException(
                message=f"统计可视化失败: {str(e)}",
                category="business_logic",
                severity="medium"
            )


class GuidelineVisualizer:
    """指南可视化器主类"""

    def __init__(self):
        self.workflow_viz = WorkflowVisualizer()
        self.evidence_viz = EvidenceVisualizer()
        self.recommendation_viz = RecommendationVisualizer()
        self.stats_viz = StatisticsVisualizer()

    async def create_visualization(
        self,
        viz_type: VisualizationType,
        data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> VisualizationResult:
        """
        创建可视化

        Args:
            viz_type: 可视化类型
            data: 可视化数据
            config: 可选配置参数

        Returns:
            VisualizationResult: 可视化结果
        """
        try:
            logger.info("开始创建可视化", extra_data={
                "viz_type": viz_type.value,
                "data_keys": list(data.keys())
            })

            if viz_type == VisualizationType.WORKFLOW_FLOWCHART:
                return await self.workflow_viz.create_workflow_flowchart(data)
            elif viz_type == VisualizationType.EVIDENCE_NETWORK:
                return await self.evidence_viz.create_evidence_network(data)
            elif viz_type == VisualizationType.RECOMMENDATION_MATRIX:
                return await self.recommendation_viz.create_recommendation_matrix(data)
            elif viz_type == VisualizationType.STATISTICS:
                return await self.stats_viz.create_statistics_dashboard(data)
            else:
                raise ValueError(f"不支持的可视化类型: {viz_type}")

        except Exception as e:
            logger.error("创建可视化失败", extra_data={
                "viz_type": viz_type.value,
                "error": str(e)
            })
            raise

    async def export_visualization(self, result: VisualizationResult, format: str = "json") -> str:
        """
        导出可视化结果

        Args:
            result: 可视化结果
            format: 导出格式 (json, html, svg)

        Returns:
            str: 导出的内容
        """
        if format == "json":
            return json.dumps(asdict(result), default=str, indent=2, ensure_ascii=False)
        elif format == "html":
            return self._generate_html_export(result)
        elif format == "svg":
            return self._generate_svg_export(result)
        else:
            raise ValueError(f"不支持的导出格式: {format}")

    def _generate_html_export(self, result: VisualizationResult) -> str:
        """生成HTML导出"""
        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{result.title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .chart-container {{ margin: 20px 0; padding: 20px; border: 1px solid #ddd; }}
        .chart-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
        .network-container {{ height: 600px; }}
        .chart-wrapper {{ height: 400px; }}
    </style>
</head>
<body>
    <h1>{result.title}</h1>
    <p>{result.description}</p>

    {self._generate_charts_html(result.charts)}

    <script>
        {self._generate_charts_script(result.charts)}
    </script>
</body>
</html>
        """
        return html_template

    def _generate_charts_html(self, charts: List[ChartData]) -> str:
        """生成图表HTML"""
        html_parts = []
        for chart in charts:
            if chart.chart_type == ChartType.NETWORK:
                html_parts.append(f"""
                <div class="chart-container">
                    <div class="chart-title">{chart.title}</div>
                    <div id="{chart.chart_id}" class="network-container"></div>
                </div>
                """)
            else:
                html_parts.append(f"""
                <div class="chart-container">
                    <div class="chart-title">{chart.title}</div>
                    <div class="chart-wrapper">
                        <canvas id="{chart.chart_id}"></canvas>
                    </div>
                </div>
                """)
        return "".join(html_parts)

    def _generate_charts_script(self, charts: List[ChartData]) -> str:
        """生成图表JavaScript"""
        script_parts = []
        for chart in charts:
            if chart.chart_type == ChartType.NETWORK:
                # Network图表脚本
                script_parts.append(f"""
                const container_{chart.chart_id} = document.getElementById('{chart.chart_id}');
                const data_{chart.chart_id} = {json.dumps(chart.data, ensure_ascii=False)};
                const network_{chart.chart_id} = new vis.Network(container_{chart.chart_id}, data_{chart.chart_id});
                """)
            else:
                # Chart.js图表脚本
                script_parts.append(f"""
                const ctx_{chart.chart_id} = document.getElementById('{chart.chart_id}').getContext('2d');
                const chart_{chart.chart_id} = new Chart(ctx_{chart.chart_id}, {{
                    type: '{chart.chart_type.value}',
                    data: {json.dumps(chart.data, ensure_ascii=False)},
                    options: {json.dumps(chart.config, ensure_ascii=False)}
                }});
                """)
        return "".join(script_parts)

    def _generate_svg_export(self, result: VisualizationResult) -> str:
        """生成SVG导出（简化实现）"""
        return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
            <text x="400" y="50" text-anchor="middle" font-size="20">{result.title}</text>
            <text x="400" y="100" text-anchor="middle" font-size="14">{result.description}</text>
            <rect x="100" y="150" width="600" height="400" fill="#f0f0f0" stroke="#333"/>
            <text x="400" y="350" text-anchor="middle" font-size="16">可视化图表区域</text>
        </svg>"""


# 全局可视化器实例
guideline_visualizer = GuidelineVisualizer()