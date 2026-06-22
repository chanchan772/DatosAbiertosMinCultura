.PHONY: install data clean train report app docs test lint format

install:
	pip install -e ".[dev]"

data:
	cinepredict download --source all

clean:
	cinepredict clean

train:
	cinepredict train

report:
	cinepredict report

app:
	streamlit run app/streamlit_app.py

docs:
	mkdocs serve

test:
	pytest

lint:
	ruff check src tests

format:
	ruff format src tests
