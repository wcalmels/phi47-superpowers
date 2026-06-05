# Contributing

    git clone https://github.com/TUCHSystems/phi47-superpowers
    pip install -e ".[dev]"
    pytest tests/ -v

## Style
- black, ruff, type hints, Google docstrings.

## Adding a diagnostic rule
1. Pick next code P0XX
2. Add check in src/phi47/linter/phi_linter.py
3. Write test in tests/unit/test_linter.py
4. Document in README.md

## License
MIT. By contributing you agree to the same license.
