PYTHON ?= python
REV ?=

.PHONY: draft xml text html validate submission-candidate release clean

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

# Produce a numbered submission-candidate rendering for IETF submission
# review. REVISION is derived from pamspec-version.json by the build
# script; a REV= override here is only used to sanity-check that the
# caller understands which revision is permitted (the script will refuse
# any mismatch).
#
# This target does NOT submit the draft and does NOT mark it as posted.
submission-candidate:
	@if [ -z "$(REV)" ]; then \
	  echo "usage: make submission-candidate REV=NN"; \
	  echo "REV must match the revision permitted by pamspec-version.json"; \
	  exit 2; \
	fi
	$(PYTHON) scripts/build_draft.py submission-candidate \
	  --revision $(REV) --confirm-submission-candidate

# Deprecated alias for submission-candidate. The same guards apply.
release: submission-candidate

clean:
	$(PYTHON) scripts/build_draft.py clean
