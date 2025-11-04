#!/usr/bin/env python3
"""
依赖关系图生成器
Dependency Diagram Generator
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from matplotlib.patches import FancyBboxPatch
import json

def create_dependency_diagram():
    """创建依赖关系可视化图"""

    # 设置中文字体
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    fig, ax = plt.subplots(1, 1, figsize=(16, 12))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')

    # 定义层次位置
    layers = {
        'API': {'y': 8.5, 'color': '#FF6B6B', 'modules': 10},
        'Services': {'y': 6.5, 'color': '#4ECDC4', 'modules': 23},
        'Workflows': {'y': 5.5, 'color': '#45B7D1', 'modules': 14},
        'Models': {'y': 4.5, 'color': '#96CEB4', 'modules': 15},
        'Schemas': {'y': 3.5, 'color': '#FFEAA7', 'modules': 7},
        'Core': {'y': 2.0, 'color': '#DDA0DD', 'modules': 15},
        'Utils': {'y': 0.8, 'color': '#F8B500', 'modules': 1},
        'Enums': {'y': 0.8, 'color': '#00B894', 'modules': 1}
    }

    # 绘制层次框
    for i, (layer_name, layer_info) in enumerate(layers.items()):
        if layer_name in ['Utils', 'Enums']:
            # Utils和Enums放在底部并排
            x_pos = 2 if layer_name == 'Utils' else 6
            width = 1.5
        else:
            x_pos = 1
            width = 8

        # 绘制层次框
        rect = FancyBboxPatch(
            (x_pos, layer_info['y'] - 0.3),
            width, 0.8,
            boxstyle="round,pad=0.1",
            facecolor=layer_info['color'],
            edgecolor='black',
            linewidth=2,
            alpha=0.7
        )
        ax.add_patch(rect)

        # 添加层次标签
        ax.text(
            x_pos + width/2,
            layer_info['y'] + 0.1,
            f"{layer_name} Layer\n({layer_info['modules']} modules)",
            ha='center',
            va='center',
            fontsize=12,
            fontweight='bold'
        )

    # 绘制依赖关系箭头
    arrows = [
        # API -> Services
        [(5, 8.2), (5, 6.8), '#FF6B6B'],
        # Services -> Core
        [(3, 6.2), (3, 2.3), '#4ECDC4'],
        [(7, 6.2), (7, 2.3), '#4ECDC4'],
        # Workflows -> Services
        [(5, 5.2), (5, 6.2), '#45B7D1'],
        # Workflows -> Core
        [(1.5, 5.2), (1.5, 2.3), '#45B7D1'],
        # Models -> Core
        [(8.5, 4.2), (8.5, 2.3), '#96CEB4'],
        # Schemas -> Core
        [(5, 3.2), (5, 2.3), '#FFEAA7'],
        # Services -> Models
        [(9, 6.2), (9, 4.8), '#4ECDC4'],
        # API -> Schemas
        [(5, 8.2), (5, 3.8), '#FF6B6B']
    ]

    for start, end, color in arrows:
        ax.annotate(
            '',
            xy=end,
            xytext=start,
            arrowprops=dict(
                arrowstyle='->',
                color=color,
                lw=2,
                alpha=0.6
            )
        )

    # 添加标题
    ax.text(
        5, 9.5,
        'CPG2PVG-AI Backend 依赖关系图',
        ha='center',
        va='center',
        fontsize=16,
        fontweight='bold'
    )

    # 添加图例
    legend_elements = [
        patches.Patch(color='#FF6B6B', alpha=0.7, label='API Layer'),
        patches.Patch(color='#4ECDC4', alpha=0.7, label='Services Layer'),
        patches.Patch(color='#45B7D1', alpha=0.7, label='Workflows Layer'),
        patches.Patch(color='#96CEB4', alpha=0.7, label='Models Layer'),
        patches.Patch(color='#FFEAA7', alpha=0.7, label='Schemas Layer'),
        patches.Patch(color='#DDA0DD', alpha=0.7, label='Core Layer'),
        patches.Patch(color='#F8B500', alpha=0.7, label='Utils'),
        patches.Patch(color='#00B894', alpha=0.7, label='Enums')
    ]

    ax.legend(
        handles=legend_elements,
        loc='upper right',
        bbox_to_anchor=(0.98, 0.98)
    )

    # 添加关键统计信息
    stats_text = """关键统计:
• 总模块数: 140
• 架构健康度: 85/100
• 循环依赖: 0个
• 接口一致性: 需改进"""

    ax.text(
        0.2, 9.5,
        stats_text,
        ha='left',
        va='top',
        fontsize=10,
        bbox=dict(boxstyle="round,pad=0.3", facecolor='lightgray', alpha=0.8)
    )

    # 保存图片
    plt.tight_layout()
    plt.savefig('dependency_diagram.png', dpi=300, bbox_inches='tight')
    plt.savefig('dependency_diagram.pdf', bbox_inches='tight')

    print("依赖关系图已生成:")
    print("- dependency_diagram.png")
    print("- dependency_diagram.pdf")

def create_coupling_heatmap():
    """创建耦合度热力图"""

    # 依赖关系数据
    dependency_data = {
        'API': {'Services': 3, 'Core': 10, 'Schemas': 7},
        'Services': {'Services': 15, 'Models': 2, 'Core': 20, 'Schemas': 8, 'Utils': 1, 'Enums': 3},
        'Models': {'Models': 3, 'Core': 5},
        'Core': {'Core': 8, 'Tasks': 1},
        'Schemas': {'Core': 2, 'Schemas': 2},
        'Workflows': {'Services': 5, 'Core': 10, 'Schemas': 2, 'Workflows': 4, 'Enums': 1},
        'Tasks': {'Services': 3, 'Models': 1, 'Core': 5, 'Schemas': 1}
    }

    layers = ['API', 'Services', 'Models', 'Core', 'Schemas', 'Workflows', 'Tasks']

    # 创建矩阵
    matrix = np.zeros((len(layers), len(layers)))
    for i, from_layer in enumerate(layers):
        for j, to_layer in enumerate(layers):
            if from_layer in dependency_data and to_layer in dependency_data[from_layer]:
                matrix[i][j] = dependency_data[from_layer][to_layer]

    # 创建热力图
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')

    # 设置标签
    ax.set_xticks(np.arange(len(layers)))
    ax.set_yticks(np.arange(len(layers)))
    ax.set_xticklabels(layers)
    ax.set_yticklabels(layers)

    # 添加数值标签
    for i in range(len(layers)):
        for j in range(len(layers)):
            if matrix[i][j] > 0:
                ax.text(j, i, f'{int(matrix[i][j])}',
                       ha="center", va="center", color="black", fontweight='bold')

    # 添加标题和标签
    ax.set_title('Module Coupling Heatmap', fontsize=14, fontweight='bold', pad=20)
    ax.set_xlabel('Depended Module', fontsize=12)
    ax.set_ylabel('Depending Module', fontsize=12)

    # 添加颜色条
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Dependency Count', fontsize=12)

    # 旋转x轴标签
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")

    plt.tight_layout()
    plt.savefig('coupling_heatmap.png', dpi=300, bbox_inches='tight')
    plt.savefig('coupling_heatmap.pdf', bbox_inches='tight')

    print("耦合度热力图已生成:")
    print("- coupling_heatmap.png")
    print("- coupling_heatmap.pdf")

if __name__ == "__main__":
    create_dependency_diagram()
    create_coupling_heatmap()