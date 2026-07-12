PYTHON ?= python
REV ?=

.PHONY: draft xml text html validate release clean

draft:
	$(PYTHON) scripts/build_draft.py all

xml:
	$(PYTHON) scripts/build_draft.py xml

text:
	$(PYTHON) scripts/build_draft.py text

html:
	$(PYTHON) scripts/build_draft.py html

validate:
	$(PYTHON) scripts/build_draft.py validate

release:
	$(PYTHON) scripts/build_draft.py release --revision $(REV)

clean:
	$(PYTHON) scripts/build_draft.py clean
