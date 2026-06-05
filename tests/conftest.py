# Copyright (c) 2025 Walter Calmels Von dem Knesebeck -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
import numpy as np
import pytest

@pytest.fixture(scope="session", autouse=True)
def seed():
    np.random.seed(42)
