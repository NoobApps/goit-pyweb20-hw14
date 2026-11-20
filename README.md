pip install -r requirements.txt

sphinx-build -b html docs docs/_build/html

pytest -v
