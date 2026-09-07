FACTORY ?= npx --yes toolfactory@0.1.2

.PHONY: build check validate package test
build:
	$(FACTORY) build
	$(FACTORY) introspect
	$(FACTORY) build
check:
	$(FACTORY) check
	uv run pytest -q
validate:
	$(FACTORY) validate
package:
	$(FACTORY) package
test:
	uv run pytest -q
