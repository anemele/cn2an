import pytest

from .an2cn import A2CMode, convert


def test_positive_integer():
    input_data = {
        0: ["零", "零", "零元整", "零"],
        1: ["一", "壹", "壹元整", "一"],
        11: ["十一", "壹拾壹", "壹拾壹元整", "一一"],
        1000000: ["一百万", "壹佰万", "壹佰万元整", "一零零零零零零"],
        1000054: [
            "一百万零五十四",
            "壹佰万零伍拾肆",
            "壹佰万零伍拾肆元整",
            "一零零零零五四",
        ],
        31000054: [
            "三千一百万零五十四",
            "叁仟壹佰万零伍拾肆",
            "叁仟壹佰万零伍拾肆元整",
            "三一零零零零五四",
        ],
        9876543298765432: [
            "九千八百七十六万五千四百三十二亿九千八百七十六万五千四百三十二",
            "玖仟捌佰柒拾陆万伍仟肆佰叁拾贰亿玖仟捌佰柒拾陆万伍仟肆佰叁拾贰",
            "玖仟捌佰柒拾陆万伍仟肆佰叁拾贰亿玖仟捌佰柒拾陆万伍仟肆佰叁拾贰元整",
            "九八七六五四三二九八七六五四三二",
        ],
        10000000000000: [
            "十万亿",
            "壹拾万亿",
            "壹拾万亿元整",
            "一零零零零零零零零零零零零零",
        ],
    }
    for key, val in input_data.items():
        assert convert(key) == val[0]
        assert convert(key, "low") == val[0]
        assert convert(key, A2CMode.LOW) == val[0]
        assert convert(key, A2CMode.UP) == val[1]
        assert convert(key, A2CMode.RMB) == val[2]
        assert convert(key, A2CMode.DIRECT) == val[3]


def test_negative_integer():
    input_data = {
        -0: ["零", "零", "零元整", "零"],
        -1: ["负一", "负壹", "负壹元整", "负一"],
        -11: ["负十一", "负壹拾壹", "负壹拾壹元整", "负一一"],
    }
    for key, val in input_data.items():
        assert convert(key) == val[0]
        assert convert(key, "low") == val[0]
        assert convert(key, A2CMode.LOW) == val[0]
        assert convert(key, A2CMode.UP) == val[1]
        assert convert(key, A2CMode.RMB) == val[2]
        assert convert(key, A2CMode.DIRECT) == val[3]


def test_float():
    input_data = {
        0.000500050005005: [
            "零点零零零五零零零五零零零五零零五",
            "零点零零零伍零零零伍零零零伍零零伍",
            "零元整",
            "零点零零零五零零零五零零零五零零五",
        ],
        0.00005: ["零点零零零零五", "零点零零零零伍", "零元整", "零点零零零零五"],
        0.4321: ["零点四三二一", "零点肆叁贰壹", "肆角叁分", "零点四三二一"],
        1000054.4321: [
            "一百万零五十四点四三二一",
            "壹佰万零伍拾肆点肆叁贰壹",
            "壹佰万零伍拾肆元肆角叁分",
            "一零零零零五四点四三二一",
        ],
        1.01: ["一点零一", "壹点零壹", "壹元零壹分", "一点零一"],
        1.2: ["一点二", "壹点贰", "壹元贰角", "一点二"],
        0.01: ["零点零一", "零点零壹", "壹分", "零点零一"],
        -0.1: ["负零点一", "负零点壹", "负壹角", "负零点一"],
        -0: ["零", "零", "零元整", "零"],
        1.10: ["一点一", "壹点壹", "壹元壹角", "一点一"],
        12.0: ["十二点零", "壹拾贰点零", "壹拾贰元整", "一二点零"],
        2.0: ["二点零", "贰点零", "贰元整", "二点零"],
        0.10: ["零点一", "零点壹", "壹角", "零点一"],
    }

    for key, val in input_data.items():
        assert convert(key) == val[0]
        assert convert(key, "low") == val[0]
        assert convert(key, A2CMode.LOW) == val[0]
        assert convert(key, A2CMode.UP) == val[1]
        assert convert(key, A2CMode.RMB) == val[2]
        assert convert(key, A2CMode.DIRECT) == val[3]


def test_error_input():
    error_input_data = ["123.1.1", "0.1零"]
    for error_data in error_input_data:
        with pytest.raises(ValueError):
            convert(error_data)
