# -*- coding:utf-8 -*-


from enum import Enum, unique


@unique
class FuzzyTimeEnum(Enum):
    # 凌晨
    day_break = 3
    # 早上
    early_morning = 8
    # 上午
    morning = 10
    # 中午
    noon = 12
    # 下午
    afternoon = 15
    # 傍晚
    night = 18
    # 晚间
    late_night = 20
    # 深夜
    mid_night = 23
