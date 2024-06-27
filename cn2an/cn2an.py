"""中文数字转阿拉伯数字

暂无较好的思路，中文数字涉及自然语言处理，情况复杂，
当前是枚举常用模式，尽可能满足需求。

"""

import re
from enum import Enum
from typing import Tuple, Union
from warnings import warn

from .an2cn import convert as ac
# fmt: off
from .conf import (NORMAL_CN_NUMBER, NUMBER_CN2AN, NUMBER_LOW_AN2CN,
                   STRICT_CN_NUMBER, UNIT_CN2AN, UNIT_LOW_AN2CN)
# fmt: on
from .utils import full_to_half_angle, t2s


class C2AMode(Enum):
    """strict 严格，normal 正常，smart 智能"""

    STRICT = 'strict'
    NORMAL = 'normal'
    SMART = 'smart'


ALL_NUM = ''.join((NUMBER_CN2AN.keys()))
ALL_UNIT = ''.join((UNIT_CN2AN.keys()))
CHECK_KEY_DICT = {
    C2AMode.STRICT: ''.join(STRICT_CN_NUMBER.values()) + "点负",
    C2AMode.NORMAL: ''.join(NORMAL_CN_NUMBER.values()) + "点负",
    C2AMode.SMART: ''.join(NORMAL_CN_NUMBER.values()) + "点负" + "01234567890.-",
}


def __get_pattern() -> dict:
    # 整数严格检查
    _0 = "[零]"
    _1_9 = "[一二三四五六七八九]"
    _10_99 = f"{_1_9}?[十]{_1_9}?"
    _1_99 = f"({_10_99}|{_1_9})"
    _100_999 = f"({_1_9}[百]([零]{_1_9})?|{_1_9}[百]{_10_99})"
    _1_999 = f"({_100_999}|{_1_99})"
    _1000_9999 = f"({_1_9}[千]([零]{_1_99})?|{_1_9}[千]{_100_999})"
    _1_9999 = f"({_1000_9999}|{_1_999})"
    _10000_99999999 = f"({_1_9999}[万]([零]{_1_999})?|{_1_9999}[万]{_1000_9999})"
    _1_99999999 = f"({_10000_99999999}|{_1_9999})"
    _100000000_9999999999999999 = (
        f"({_1_99999999}[亿]([零]{_1_99999999})?|{_1_99999999}[亿]{_10000_99999999})"
    )
    _1_9999999999999999 = f"({_100000000_9999999999999999}|{_1_99999999})"

    str_int_pattern = f"^({_0}|{_1_9999999999999999})$"
    nor_int_pattern = f"^({_0}|{_1_9999999999999999})$"
    str_dec_pattern = "^[零一二三四五六七八九]{0,15}[一二三四五六七八九]$"
    nor_dec_pattern = "^[零一二三四五六七八九]{0,16}$"

    strict_tab = {ord(key): val for key, val in STRICT_CN_NUMBER.items()}
    normal_tab = {ord(key): val for key, val in NORMAL_CN_NUMBER.items()}

    str_int_pattern = str_int_pattern.translate(strict_tab)
    str_dec_pattern = str_dec_pattern.translate(strict_tab)
    nor_int_pattern = nor_int_pattern.translate(normal_tab)
    nor_dec_pattern = nor_dec_pattern.translate(normal_tab)

    pattern_dict = {
        C2AMode.STRICT: {
            "int": re.compile(str_int_pattern),
            "dec": re.compile(str_dec_pattern),
        },
        C2AMode.NORMAL: {
            "int": re.compile(nor_int_pattern),
            "dec": re.compile(nor_dec_pattern),
        },
    }
    return pattern_dict


PATTERN_DICT = __get_pattern()


class Pattern:
    yjf = re.compile(fr"^.*?[元圆][{ALL_NUM}]角([{ALL_NUM}]分)?$")
    pattern1 = re.compile(fr"^-?\d+(\.\d+)?[{ALL_UNIT}]?$")
    all_num = re.compile(f"^[{ALL_NUM}]+$")
    # "十?" is for special case "十一万三"
    speaking_mode = re.compile(f"^([{ALL_NUM}]{{0,2}}[{ALL_UNIT}])+[{ALL_NUM}]$")


def __check_input_data_is_valid(
    check_data: str, mode: C2AMode
) -> Tuple[int, str, str, bool]:
    # 去除 元整、圆整、元正、圆正
    stop_words = ["元整", "圆整", "元正", "圆正"]
    for word in stop_words:
        if check_data[-2:] == word:
            check_data = check_data[:-2]

    # 去除 元、圆
    if mode != C2AMode.STRICT:
        normal_stop_words = ["圆", "元"]
        for word in normal_stop_words:
            if check_data[-1] == word:
                check_data = check_data[:-1]

    # 处理元角分
    result = Pattern.yjf.search(check_data)
    if result:
        check_data = check_data.replace("元", "点").replace("角", "").replace("分", "")

    # 处理特殊问法：一千零十一 一万零百一十一
    if "零十" in check_data:
        check_data = check_data.replace("零十", "零一十")
    if "零百" in check_data:
        check_data = check_data.replace("零百", "零一百")

    for data in check_data:
        if data not in CHECK_KEY_DICT[mode]:
            raise ValueError(f"当前为{mode}模式，输入的数据不在转化范围内：{data}！")

    # 确定正负号
    if check_data[0] == "负":
        check_data = check_data[1:]
        sign = -1
    else:
        sign = 1

    if "点" in check_data:
        split_data = check_data.split("点")
        if len(split_data) == 2:
            integer_data, decimal_data = split_data
            # 将 smart 模式中的阿拉伯数字转化成中文数字
            if mode == C2AMode.SMART:
                integer_data = re.sub(r"\d+", lambda x: ac(x.group()), integer_data)
                decimal_data = re.sub(
                    r"\d+", lambda x: __copy_num(x.group()), decimal_data
                )
                mode = C2AMode.NORMAL
        else:
            raise ValueError("数据中包含不止一个点！")
    else:
        integer_data = check_data
        decimal_data = None
        # 将 smart 模式中的阿拉伯数字转化成中文数字
        if mode == C2AMode.SMART:
            # 10.1万 10.1
            result1 = Pattern.pattern1.search(integer_data)
            if result1:
                if result1.group() == integer_data:
                    if integer_data[-1] in UNIT_CN2AN.keys():
                        output = int(
                            float(integer_data[:-1]) * UNIT_CN2AN[integer_data[-1]]
                        )
                    else:
                        output = float(integer_data)
                    return 0, output, None, None

            integer_data = re.sub(r"\d+", lambda x: ac(x.group()), integer_data)
            mode = C2AMode.NORMAL

    result_int = PATTERN_DICT[mode]["int"].search(integer_data)
    if result_int:
        if result_int.group() == integer_data:
            if decimal_data is not None:
                result_dec = PATTERN_DICT[mode]["dec"].search(decimal_data)
                if result_dec:
                    if result_dec.group() == decimal_data:
                        return sign, integer_data, decimal_data, False
            else:
                return sign, integer_data, decimal_data, False
    else:
        if mode == C2AMode.STRICT:
            raise ValueError(f"不符合格式的数据：{integer_data}")
        elif mode == C2AMode.NORMAL:
            # 纯数模式：一二三
            result_all_num = Pattern.all_num.search(integer_data)
            if result_all_num:
                if result_all_num.group() == integer_data:
                    if decimal_data is not None:
                        result_dec = PATTERN_DICT[mode]["dec"].search(decimal_data)
                        if result_dec:
                            if result_dec.group() == decimal_data:
                                return sign, integer_data, decimal_data, True
                    else:
                        return sign, integer_data, decimal_data, True

            # 口语模式：一万二，两千三，三百四，十三万六，一百二十五万三
            result_speaking_mode = Pattern.speaking_mode.search(integer_data)
            if (
                len(integer_data) >= 3
                and result_speaking_mode
                and result_speaking_mode.group() == integer_data
            ):
                # len(integer_data)>=3: because the minimum length of integer_data that can be matched is 3
                # to find the last unit
                last_unit = result_speaking_mode.groups()[-1][-1]
                _unit = UNIT_LOW_AN2CN[UNIT_CN2AN[last_unit] // 10]
                integer_data = integer_data + _unit
                if decimal_data is not None:
                    result_dec = PATTERN_DICT[mode]["dec"].search(decimal_data)
                    if result_dec:
                        if result_dec.group() == decimal_data:
                            return sign, integer_data, decimal_data, False
                else:
                    return sign, integer_data, decimal_data, False

    raise ValueError(f"不符合格式的数据：{check_data}")


def __copy_num(num: str) -> str:
    return ''.join(NUMBER_LOW_AN2CN[int(bit)] for bit in num)


def __integer_convert(integer_data: str) -> int:
    # 核心
    output_integer = 0
    unit = 1
    ten_thousand_unit = 1
    for index, cn_num in enumerate(reversed(integer_data)):
        # 数值
        if cn_num in NUMBER_CN2AN:
            num = NUMBER_CN2AN[cn_num]
            output_integer += num * unit
        # 单位
        elif cn_num in UNIT_CN2AN:
            unit = UNIT_CN2AN[cn_num]
            # 判断出万、亿、万亿
            if unit % 10000 == 0:
                # 万 亿
                if unit > ten_thousand_unit:
                    ten_thousand_unit = unit
                # 万亿
                else:
                    ten_thousand_unit = unit * ten_thousand_unit
                    unit = ten_thousand_unit

            if unit < ten_thousand_unit:
                unit = unit * ten_thousand_unit

            if index == len(integer_data) - 1:
                output_integer += unit
        else:
            raise ValueError(f"{cn_num} 不在转化范围内")

    return int(output_integer)


def __decimal_convert(decimal_data: str) -> float:
    len_decimal_data = len(decimal_data)

    if len_decimal_data > 16:
        warn(f"注意：小数部分长度为 {len_decimal_data} ，将自动截取前 16 位有效精度！")
        decimal_data = decimal_data[:16]
        len_decimal_data = 16

    output_decimal = 0
    for index in range(len(decimal_data) - 1, -1, -1):
        unit_key = NUMBER_CN2AN[decimal_data[index]]
        output_decimal += unit_key * 10 ** -(index + 1)

    # 处理精度溢出问题
    output_decimal = round(output_decimal, len_decimal_data)

    return output_decimal


def __direct_convert(data: str) -> int:
    output_data = 0
    for index in range(len(data) - 1, -1, -1):
        unit_key = NUMBER_CN2AN[data[index]]
        output_data += unit_key * 10 ** (len(data) - index - 1)

    return output_data


def convert(
    number: str, mode: Union[C2AMode, str] = C2AMode.STRICT
) -> Union[float, int]:
    """中文数字转阿拉伯数字

    :param number: 中文数字、阿拉伯数字、中文数字和阿拉伯数字
    :param mode:
    :return: 阿拉伯数字
    """
    if number == "":
        raise ValueError("输入数据为空！")

    if isinstance(mode, str):
        try:
            mode = C2AMode(mode)
        except ValueError:
            raise ValueError(f"不支持该模式：{mode}")

    # 数据预处理：
    # 1. 繁体转简体
    # 2. 全角转半角
    number = t2s(number)
    number = full_to_half_angle(number)

    # 特殊转化 廿
    number = number.replace("廿", "二十").replace('卅', '三十')

    # 检查输入数据是否有效
    sign, integer_data, decimal_data, is_all_num = __check_input_data_is_valid(
        number, mode
    )

    # smart 下的特殊情况
    if sign == 0:
        return integer_data

    if not is_all_num:
        if decimal_data is None:
            output = __integer_convert(integer_data)
        else:
            output = __integer_convert(integer_data) + __decimal_convert(decimal_data)
            # fix 1 + 0.57 = 1.5699999999999998
            output = round(output, len(decimal_data))
    else:
        if decimal_data is None:
            output = __direct_convert(integer_data)
        else:
            output = __direct_convert(integer_data) + __decimal_convert(decimal_data)
            # fix 1 + 0.57 = 1.5699999999999998
            output = round(output, len(decimal_data))

    return sign * output
