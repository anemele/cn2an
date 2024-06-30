from .utils import float_to_str


def test_float_to_str():
    assert float_to_str(0.00005) == '0.00005'
    assert float_to_str(1.00005) == '1.00005'
    assert float_to_str(1234.4321) == '1234.4321'
    assert float_to_str(-0.00005) == '-0.00005'
    assert float_to_str(-1.00005) == '-1.00005'
    assert float_to_str(-1234.4321) == '-1234.4321'
    assert float_to_str(1.10) == '1.1'
