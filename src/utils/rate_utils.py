# src/utils/rate_utils.py
"""
爆率计算工具
"""

import math
from fractions import Fraction


def calculate_expected_kills(rate: float, confidence: float = 0.95) -> int:
    """
    计算期望击杀数
    :param rate: 爆率 (0-1)
    :param confidence: 置信度 (0-1)
    :return: 期望击杀数
    """
    if rate <= 0:
        return float('inf')
    
    if confidence >= 1:
        confidence = 0.999
    
    # 计算在给定置信度下需要击杀的数量
    # P(至少掉落一次) = 1 - (1 - rate)^n >= confidence
    # 解得 n >= log(1 - confidence) / log(1 - rate)
    
    try:
        n = math.log(1 - confidence) / math.log(1 - rate)
        return math.ceil(n)
    except (ValueError, ZeroDivisionError):
        return float('inf')


def rate_to_fraction(rate: float) -> str:
    """将爆率转换为最接近的分数形式"""
    if rate <= 0:
        return "0"
    elif rate >= 1:
        return "1/1"
    
    # 使用Fraction类
    fraction = Fraction(rate).limit_denominator(1000000)
    return f"{fraction.numerator}/{fraction.denominator}"


def combine_rates(rates: list) -> float:
    """合并多个独立爆率（至少掉落一个的概率）"""
    if not rates:
        return 0.0
    
    # P(至少掉落一个) = 1 - ∏(1 - rate_i)
    prob_no_drop = 1.0
    for rate in rates:
        if 0 <= rate <= 1:
            prob_no_drop *= (1 - rate)
    
    return 1 - prob_no_drop


def calculate_drop_chance(rate: float, kills: int) -> float:
    """
    计算击杀n次至少掉落一次的概率
    :param rate: 单次击杀爆率
    :param kills: 击杀次数
    :return: 至少掉落一次的概率
    """
    if rate <= 0 or kills <= 0:
        return 0.0
    
    return 1 - math.pow(1 - rate, kills)


def format_rate_for_display(rate: float) -> dict:
    """格式化爆率用于显示"""
    if rate <= 0:
        return {
            'percent': '0%',
            'fraction': '0',
            'inverse': '∞',
            'expected': '∞'
        }
    
    return {
        'percent': f"{rate*100:.6f}%",
        'fraction': rate_to_fraction(rate),
        'inverse': f"1/{int(1/rate)}" if rate > 0 else "∞",
        'expected': str(int(1/rate)) if rate > 0 else "∞"
    }