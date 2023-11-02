SOURCES := \
	utils/commons.py \
	utils/r2m.py \

default: style

flake8:
	flake8 $(SOURCES)

isort-diff:
	isort --diff $(SOURCES)

isort:
	isort $(SOURCES)

style: flake8 isort-diff
