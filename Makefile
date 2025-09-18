.PHONY: venv install index run clean

venv:
	python -m venv .venv

install: venv
	. .venv/bin/activate && pip install -r requirements.txt

index:
	. .venv/bin/activate && python build_index.py

run:
	. .venv/bin/activate && python app.py

clean:
	rm -rf .venv index __pycache__ */__pycache__
