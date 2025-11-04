#!/usr/bin/env python3
"""
Fix Agents Validation Methods
修复智能体验证方法
"""

from pathlib import Path

project_root = Path(__file__).parent.parent

def add_validation_methods():
    """为所有智能体类添加validate_result方法"""
    file_path = project_root / "app/services/medical_agents.py"

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 为PreventionAgent添加验证方法
    prevention_validation = """
    async def validate_result(self, result: AgentResult) -> bool:
        \"\"\"验证预防结果\"\"\"
        return (
            result.status == AgentStatus.COMPLETED and
            result.confidence_score > 0.5
        )

"""

    # 为MonitoringAgent添加验证方法
    monitoring_validation = """
    async def validate_result(self, result: AgentResult) -> bool:
        \"\"\"验证监测结果\"\"\"
        return (
            result.status == AgentStatus.COMPLETED and
            result.confidence_score > 0.6
        )

"""

    # 为SpecialPopulationsAgent添加验证方法
    special_populations_validation = """
    async def validate_result(self, result: AgentResult) -> bool:
        \"\"\"验证特殊人群结果\"\"\"
        return (
            result.status == AgentStatus.COMPLETED and
            result.confidence_score > 0.7
        )

"""

    # 在PreventionAgent类定义后添加验证方法
    content = content.replace(
        "class PreventionAgent(BaseMedicalAgent):",
        f"class PreventionAgent(BaseMedicalAgent):{prevention_validation}"
    )

    # 在MonitoringAgent类定义后添加验证方法
    content = content.replace(
        "class MonitoringAgent(BaseMedicalAgent):",
        f"class MonitoringAgent(BaseMedicalAgent):{monitoring_validation}"
    )

    # 在SpecialPopulationsAgent类定义后添加验证方法
    content = content.replace(
        "class SpecialPopulationsAgent(BaseMedicalAgent):",
        f"class SpecialPopulationsAgent(BaseMedicalAgent):{special_populations_validation}"
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print("Added validation methods to all agent classes")

if __name__ == "__main__":
    add_validation_methods()