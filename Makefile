SOURCE_DIR=src

default: all

all: test

test:
	# Run unit tests
	cd $(SOURCE_DIR) && \
	python -m unittest discover
	# Success


.PHONY : all test run
