from typing import Callable

import opencc

t2s: Callable[[str], str] = opencc.OpenCC('t2s').convert


def full_to_half_angle(s: str) -> str:
    """
    全角字符：0xFF01 ~ 0xFF5E
    半角字符：0x0021~ 0x007E
    全角空格：0x3000
    半角空格：0x0020
    """
    tab = dict(zip(range(0xFF01, 0xFF5E + 1), range(0x0021, 0x007E + 1)))
    tab.update({0x3000: 0x0020})
    return s.translate(tab)


def float_to_str(f: float) -> str:
    """
    异常情况：
    str(0.00005) == '5e-05'
    """
    ret = str(f)
    e_pos = ret.find('e')
    if e_pos == -1:
        return ret

    base = ret[:e_pos]
    if f < 0:
        sign = '-'
        base = base[1:]
    else:
        sign = ''
    # 如果转换成了科学计数法，此处的幂应该都是负数
    power = -int(ret[e_pos + 1 :])
    zeros = '0' * (power - 1)
    return f'{sign}0.{zeros}{base}'
