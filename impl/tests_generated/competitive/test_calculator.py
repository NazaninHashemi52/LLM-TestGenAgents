from impl.cut.calculator import *



def test_agent2_negative_exponent_power():
    """Test power with negative exponent to check float result."""
    assert power(2, -1) == 0.5

def test_agent2_large_integer_modulo():
    """Test modulo with very large integers for overflow or precision issues."""
    assert modulo(10**18, 3) == 1

def test_agent2_sqrt_zero():
    """Test sqrt with zero input to ensure it returns zero without error."""
    assert sqrt(0) == 0.0

def test_agent2_integer_divide_negative():
    """Test integer division with negative numbers to check floor behavior."""
    assert integer_divide(-7, 3) == -3

def test_agent2_history_after_clear():
    """Test that clear_history resets history and accumulator correctly."""
    calc = Calculator()
    calc.add(1, 2)
    calc.clear_history()
    assert calc.operation_count() == 0
    assert calc.accumulator == 0.0
    assert calc.last_result() is None

    import pytest
from impl.cut.calculator import *


def test_competitive_power_zero_exponent():
    """Verify that any non-zero number raised to zero returns one."""
    assert power(5, 0) == 1
    assert power(-3, 0) == 1

    calc = Calculator()
    assert calc.power(5, 0) == 1
    assert calc.power(-3, 0) == 1


def test_competitive_divide_negative_numbers():
    """Verify division behavior with negative operands."""
    assert divide(-10, 2) == -5
    assert divide(10, -2) == -5
    assert divide(-10, -2) == 5

    calc = Calculator()
    assert calc.divide(-10, 2) == -5
    assert calc.divide(10, -2) == -5
    assert calc.divide(-10, -2) == 5


def test_competitive_modulo_negative_numbers():
    """Verify modulo behavior with negative operands follows Python semantics."""
    assert modulo(-7, 3) == 2
    assert modulo(7, -3) == -2

    calc = Calculator()
    assert calc.modulo(-7, 3) == 2
    assert calc.modulo(7, -3) == -2


def test_competitive_chained_calculator_history():
    """Verify calculator history is updated correctly across multiple operations."""
    calc = Calculator()

    assert calc.add(4, 6) == 10
    assert calc.multiply(10, 2) == 20
    assert calc.divide(20, 4) == 5

    assert calc.operation_count() == 3
    assert calc.last_result() == 5


def test_competitive_clear_history_resets_state():
    """Verify clear_history resets both operation history and accumulator state."""
    calc = Calculator()

    calc.add(3, 7)
    calc.multiply(2, 5)
    calc.clear_history()

    assert calc.operation_count() == 0
    assert calc.last_result() is None
    assert calc.accumulator == 0.0


def test_competitive_non_numeric_inputs_raise_type_error():
    """Verify arithmetic functions reject non-numeric inputs consistently."""
    invalid_inputs = [
        ("1", 2),
        (None, 2),
        ([1], 2),
    ]

    for left, right in invalid_inputs:
        with pytest.raises(TypeError):
            add(left, right)

        with pytest.raises(TypeError):
            subtract(left, right)

        with pytest.raises(TypeError):
            multiply(left, right)