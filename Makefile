DRAFT_BASE=draft-infantado-agent-memory-architecture
REV=00
SRC=$(DRAFT_BASE).md
XML=$(DRAFT_BASE)-$(REV).xml
TXT=$(DRAFT_BASE)-$(REV).txt
HTML=$(DRAFT_BASE)-$(REV).html
PYTHON ?= python

.PHONY: draft xml text html validate clean validate-json validate-metadata

draft: xml text html validate

xml:
	kramdown-rfc --v3 $(SRC) > $(XML)

text: xml
	xml2rfc --text --out $(TXT) $(XML)

html: xml
	xml2rfc --html --out $(HTML) $(XML)

validate: xml text html validate-json validate-metadata
	xml2rfc --v3 --strict $(XML) --out /tmp/pama-validated.xml

validate-json:
	$(PYTHON) -m json.tool schemas/memory-object.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/memory-event.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/memory-scope.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/actor.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/provenance.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/relationship.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/embedding-space.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/query.schema.json > /dev/null
	$(PYTHON) -m json.tool schemas/error.schema.json > /dev/null
	$(PYTHON) -m json.tool examples/claim.json > /dev/null
	$(PYTHON) -m json.tool examples/decision.json > /dev/null
	$(PYTHON) -m json.tool examples/task.json > /dev/null
	$(PYTHON) -m json.tool examples/artifact.json > /dev/null
	$(PYTHON) -m json.tool examples/version-chain.json > /dev/null
	$(PYTHON) -m json.tool examples/lifecycle-transition.json > /dev/null
	$(PYTHON) -m json.tool examples/semantic-query.json > /dev/null
	$(PYTHON) -m json.tool examples/concurrent-update-conflict.json > /dev/null
	$(PYTHON) -m jsonschema -i examples/claim.json schemas/memory-object.schema.json
	$(PYTHON) -m jsonschema -i examples/decision.json schemas/memory-object.schema.json
	$(PYTHON) -m jsonschema -i examples/task.json schemas/memory-object.schema.json
	$(PYTHON) -m jsonschema -i examples/artifact.json schemas/memory-object.schema.json
	$(PYTHON) -m jsonschema -i examples/semantic-query.json schemas/query.schema.json

validate-metadata:
	$(PYTHON) scripts/validate_repository.py

clean:
	rm -f $(XML) $(TXT) $(HTML)
