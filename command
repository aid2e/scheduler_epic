python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip black ruff

flake8 scheduler/
black scheduler/
ruff check scheduler/ --fix
