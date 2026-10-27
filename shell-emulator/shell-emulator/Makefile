PYTHON ?= python3

.PHONY: run test lint vfs demo

run:
	./run.sh

test:
	$(PYTHON) -m unittest discover -s tests -t . -v

lint:
	$(PYTHON) -m flake8 src tests
	$(PYTHON) -m radon cc -n C src

vfs:
	$(PYTHON) scripts/make_vfs.py

demo: vfs
	./scripts/stage5.sh
