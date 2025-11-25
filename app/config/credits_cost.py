# -*- coding: utf-8 -*-
"""
算力消耗配置
定义不同任务类型和配置下的算力消耗
"""
from typing import Dict


# 基础算力消耗（按编辑模式）
BASE_CREDITS_COST: Dict[str, int] = {
    "HEAD_SWAP": 40,           # AI 换头：40 算力
    "BACKGROUND_CHANGE": 30,   # AI 换背景：30 算力
    "POSE_CHANGE": 50,         # AI 换姿势：50 算力（最复杂）
}


# 图片质量加成（乘数）
QUALITY_MULTIPLIER: Dict[str, float] = {
    "standard": 1.0,    # 标准质量：无加成
    "high": 1.5,        # 高清：1.5倍
    "ultra": 2.0,       # 超高清：2倍
}


# 尺寸加成（乘数）
SIZE_MULTIPLIER: Dict[str, float] = {
    "small": 1.0,       # 小图：无加成
    "medium": 1.2,      # 中图：1.2倍
    "large": 1.5,       # 大图：1.5倍
    "xlarge": 2.0,      # 超大图：2倍
}


def calculate_task_credits(
    mode: str,
    quality: str = "standard",
    size: str = "medium"
) -> int:
    """
    计算任务所需算力
    
    Args:
        mode: 编辑模式（HEAD_SWAP / BACKGROUND_CHANGE / POSE_CHANGE）
        quality: 图片质量（standard / high / ultra）
        size: 图片尺寸（small / medium / large / xlarge）
        
    Returns:
        所需算力点数
    """
    # 获取基础算力
    base_credits = BASE_CREDITS_COST.get(mode, 40)
    
    # 获取质量乘数
    quality_mult = QUALITY_MULTIPLIER.get(quality, 1.0)
    
    # 获取尺寸乘数
    size_mult = SIZE_MULTIPLIER.get(size, 1.2)
    
    # 计算总算力（向上取整）
    total_credits = int(base_credits * quality_mult * size_mult)
    
    return total_credits


def get_mode_base_credits(mode: str) -> int:
    """
    获取模式的基础算力消耗
    
    Args:
        mode: 编辑模式
        
    Returns:
        基础算力
    """
    return BASE_CREDITS_COST.get(mode, 40)


# 示例计算
if __name__ == "__main__":
    print("算力消耗示例：")
    print("=" * 60)
    
    # 示例 1: 标准换头
    cost1 = calculate_task_credits("HEAD_SWAP", "standard", "medium")
    print(f"AI 换头（标准质量，中等尺寸）: {cost1} 算力")
    
    # 示例 2: 高清换背景
    cost2 = calculate_task_credits("BACKGROUND_CHANGE", "high", "large")
    print(f"AI 换背景（高清质量，大尺寸）: {cost2} 算力")
    
    # 示例 3: 超高清换姿势
    cost3 = calculate_task_credits("POSE_CHANGE", "ultra", "xlarge")
    print(f"AI 换姿势（超高清质量，超大尺寸）: {cost3} 算力")
    
    print("\n不同套餐可处理次数：")
    print("=" * 60)
    
    # 假设使用标准配置（HEAD_SWAP, standard, medium）
    standard_cost = calculate_task_credits("HEAD_SWAP", "standard", "medium")
    
    plans = {
        "STARTER": 2000,
        "BASIC": 5000,
        "PRO": 12000,
        "ULTIMATE": 30000
    }
    
    for plan_name, credits in plans.items():
        count = credits // standard_cost
        print(f"{plan_name} 套餐（{credits} 算力）→ 约 {count} 次标准处理")

