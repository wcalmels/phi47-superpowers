# Copyright (c) 2025 wcalmels -- TUCH Systems Research Laboratory
# SPDX-License-Identifier: MIT
import textwrap
import pytest
from phi47.linter.phi_linter import Phi47Linter

ZOMBIE = textwrap.dedent('''
    def alpha(): return 1
    def beta():  return 2
    def gamma(): return 3
''')

CONNECTED = textwrap.dedent('''
    from typing import List
    def validate(data: dict) -> bool:
        return "id" in data
    def transform(data: dict) -> dict:
        if not validate(data): return {}
        return {"id": data["id"], "v": data["id"] * 2}
    def aggregate(items: List[dict]) -> dict:
        return {"n": len(items), "items": [transform(i) for i in items]}
''')

@pytest.fixture
def linter():
    return Phi47Linter()

@pytest.fixture
def zombie_file(tmp_path):
    p = tmp_path / "zombie.py"
    p.write_text(ZOMBIE, encoding="utf-8")
    return str(p)

@pytest.fixture
def connected_file(tmp_path):
    p = tmp_path / "connected.py"
    p.write_text(CONNECTED, encoding="utf-8")
    return str(p)

def test_zombie_detected(linter, zombie_file):
    codes = [d.code for d in linter.lint_file(zombie_file)]
    assert "P002" in codes

def test_connected_no_zombie(linter, connected_file):
    zombies = [d for d in linter.lint_file(connected_file) if d.code == "P002"]
    assert len(zombies) == 0

def test_syntax_error(linter, tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("def foo(:\n", encoding="utf-8")
    assert linter.lint_file(str(bad))[0].code == "P000"

def test_to_dict(linter, zombie_file):
    d = linter.lint_file(zombie_file)[0].to_dict()
    assert "code" in d and "message" in d

def test_lint_directory(linter, tmp_path):
    (tmp_path / "m.py").write_text(ZOMBIE, encoding="utf-8")
    assert len(linter.lint_directory(str(tmp_path))) >= 1
