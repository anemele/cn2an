"""阿拉伯数字转中文数字

输入三种类型：
int float str
输入四种模式：
low up rmb direct

int 转为 int_str
low up direct 直接转换
rmb 经过 up 转换后加上“元整”

float 转为 float_str
分为 int_str 和 dec_str
low up direct 直接转换
rmb 经过 up 转换，然后截取 dec_str 2 位，如果不为零，分别加上元角分

str 经过测试是数字
然后如果是 int 数字则走 int
是 float 数字则走 float

注意：
字符串比数字更精确，对于 '-0' , '1.10' 等情况如实生成，不作取舍，
即 “负零” 、 “一点一零” 。
但是对于人民币模式还是要取舍，包括小数截取两位、舍去尾零等。
"""

from enum import Enum
from functools import wraps
from typing import Callable, Union

# fmt: off
from .conf import (NUMBER_LOW, NUMBER_LOW_AN2CN, NUMBER_UP_AN2CN,
                   UNIT_LOW_ORDER_AN2CN, UNIT_UP_ORDER_AN2CN)
# fmt: on
from .utils import float_to_str


class A2CMode(Enum):
    """low 小写数字，up 大写数字，rmb 人民币大写，direct 直接转化"""

    LOW = 'low'
    UP = 'up'
    RMB = 'rmb'
    DIRECT = 'direct'


NUMBER = "0123456789"


def __direct_convert(data: str) -> str:
    # 0: 0x30
    tab = {i + 0x30: c for i, c in enumerate(NUMBER_LOW)}
    tab.update({ord('.'): "点"})
    return data.translate(tab)


def __integer_convert(data: str, mode: A2CMode) -> str:
    r"""
    私有方法，由开发者保证输入合法性。
    data 是 \d+ 全匹配
    mode 只取 LOW 和 UP
    """
    if mode == A2CMode.LOW:
        numeral_list = NUMBER_LOW_AN2CN
        unit_list = UNIT_LOW_ORDER_AN2CN
    elif mode == A2CMode.UP:
        numeral_list = NUMBER_UP_AN2CN
        unit_list = UNIT_UP_ORDER_AN2CN
    else:
        raise ValueError(f"error mode: {mode}")

    # 去除前面的 0，比如 007 => 7
    data = data.lstrip('0')

    len_integer_data = len(data)
    if len_integer_data > len(unit_list):
        raise ValueError(f"超出数据范围，最长支持 {len(unit_list)} 位")

    output_an = ""
    for i, d in enumerate(data):
        if int(d):
            output_an += numeral_list[int(d)] + unit_list[len_integer_data - i - 1]
        else:
            if not (len_integer_data - i - 1) % 4:
                output_an += numeral_list[int(d)] + unit_list[len_integer_data - i - 1]

            if i > 0 and not output_an[-1] == "零":
                output_an += numeral_list[int(d)]

    output_an = (
        output_an.replace("零零", "零")
        .replace("零万", "万")
        .replace("零亿", "亿")
        .replace("亿万", "亿")
        .strip("零")
    )

    # 解决「一十几」问题
    if output_an[:2] in {"一十"}:
        output_an = output_an[1:]

    # 0 - 1 之间的小数
    if not output_an:
        output_an = "零"

    return output_an


def __decimal_convert(data: str, mode: A2CMode) -> str:
    r"""
    私有方法，由开发者保证输入合法性。
    data 是 \d+ 全匹配
    mode 只取 LOW 和 UP
    """
    if mode == A2CMode.LOW:
        numeral_list = NUMBER_LOW_AN2CN
    elif mode == A2CMode.UP:
        numeral_list = NUMBER_UP_AN2CN
    else:
        raise ValueError(f"error mode: {mode}")

    output = ''.join(numeral_list[int(bit)] for bit in data)

    return output


def _process_sign(func: Callable[[str, A2CMode], str]):
    @wraps(func)
    def wrapper(data: str, mode: A2CMode) -> str:
        if data[0] == '-':
            return '负' + func(data[1:], mode)

        return func(data, mode)

    return wrapper


@_process_sign
def _convert_integer(data: str, mode: A2CMode) -> str:
    if mode == A2CMode.DIRECT:
        return __direct_convert(data)
    if mode == A2CMode.RMB:
        return __integer_convert(data, A2CMode.UP) + '元整'

    return __integer_convert(data, mode)


@_process_sign
def _convert_float(data: str, mode: A2CMode) -> str:
    if mode == A2CMode.DIRECT:
        return __direct_convert(data)

    int_str, dec_str = data.split('.', 1)

    if mode == A2CMode.RMB:
        int_part = __integer_convert(int_str, A2CMode.UP).lstrip('零')
        # 人民币小数最多保留两位
        dec_part = __decimal_convert(dec_str, A2CMode.UP)[:2].rstrip('零')

        # 以下逻辑：
        # 如果小数部分为空且整数部分为空，则返回“零元整”
        # 如果小数部分为空且整数部分不为空，则返回“XX元整”
        # 如果小数部分不为空且整数部分为空，则……
        # 如果小数部分不为空且整数部分不为空，则……
        if len(dec_part) == 0:
            if len(int_part) == 0:
                return '零元整'
            return int_part + '元整'

        ret = []

        if len(int_part) == 0:
            for c, u in zip(dec_part, '角分'):
                if c == '零':
                    continue
                ret.append(c)
                ret.append(u)
            if len(ret) == 0:
                return '零元整'
            return ''.join(ret)

        ret.append(int_part)
        ret.append('元')
        for c, u in zip(dec_part, '角分'):
            ret.append(c)
            if c != '零':
                ret.append(u)
        return ''.join(ret)

    int_part = __integer_convert(int_str, mode)
    dec_part = __decimal_convert(dec_str, mode)
    return f'{int_part}点{dec_part}'


def convert(
    number: Union[str, int, float], mode: Union[A2CMode, str] = A2CMode.LOW
) -> str:
    """阿拉伯数字转中文数字

    :param number: 阿拉伯数字
    :param mode:
    :return: 中文数字
    """
    if isinstance(mode, str):
        try:
            mode = A2CMode(mode)
        except ValueError:
            raise ValueError(f"不支持该模式：{mode}")

    if isinstance(number, int):
        return _convert_integer(str(number), mode)
    elif isinstance(number, float):
        return _convert_float(float_to_str(number), mode)

    try:
        # 如果是字符串但不是数字，这里会抛出 ValueError
        # 如果不是数字或者字符串，这里会抛出 TypeError
        float(number)
    except ValueError:
        raise ValueError(f'不是合法的数字：{number}')
    except TypeError:
        raise TypeError(f'不是支持的类型：{type(number)}')

    # 这里不能使用 str.isdigit 判断，因为负整数返回 False
    if number.find('.') == -1:
        return _convert_integer(number, mode)
    else:
        return _convert_float(number, mode)
