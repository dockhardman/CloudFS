install_all:
	poetry install -E all

upgrade_dependencies:
	poetry update
	poetry export --without-hashes -f requirements.txt --output requirements.txt
	poetry export --without-hashes -f requirements.txt --with dev --extras all --output requirements_all.txt

format_all:
	isort . --skip setup.py
	black --exclude setup.py .
