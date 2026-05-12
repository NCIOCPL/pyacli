format:
	python -m isort .
	python -m black .

lint:
	-python -m isort . -c
	-python -m black . --check
	pylint . --recursive=y

# Ensure the local src-layout package wins over any installed pyacli copy.
test:
	PYTHONPATH=src coverage run -m unittest discover -s ./
	coverage report

all:
	make format
	make lint
	make test
