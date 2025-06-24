python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip black ruff
pip install idds-client idds-common idds-workflow panda-client

flake8 scheduler/
black scheduler/
ruff check scheduler/ --fix
