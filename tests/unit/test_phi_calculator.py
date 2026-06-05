# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
import numpy as np
import pytest
from phi47.core.phi_calculator import PhiCalculator

@pytest.fixture
def calc():
    return PhiCalculator()

def test_phi_nonnegative(calc):
    phi, _ = calc.calculate(np.random.rand(5, 5))
    assert phi >= 0.0

def test_phi_cyclic(calc):
    m = np.array([[0,1,0],[0,0,1],[1,0,0]], dtype=float)
    phi, _ = calc.calculate(m)
    assert phi > 0.0

def test_raises_non_square(calc):
    with pytest.raises(ValueError):
        calc.calculate(np.ones((3, 4)))

def test_exact_small(calc):
    phi, meta = calc.calculate(np.random.rand(4, 4), method="exact")
    assert meta["method"] == "exact"
    assert phi >= 0.0

@pytest.mark.parametrize("n", [3, 6, 10, 20])
def test_various_sizes(n, calc):
    phi, _ = calc.calculate(np.random.rand(n, n))
    assert 0.0 <= phi < 1e6
