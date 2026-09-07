# Developer tooling only. The installed Codex plugin executes none of this.
include dev.toolfactory/source.mk

FACTORY_DIR := $(CURDIR)/.cache/toolfactory
FACTORY_READY := $(FACTORY_DIR)/.ready-$(TOOLFACTORY_REVISION)

.PHONY: prepare build check validate package test

prepare: $(FACTORY_READY)

$(FACTORY_READY): dev.toolfactory/source.mk
	@test -d "$(FACTORY_DIR)/.git" || git clone --no-checkout https://github.com/GoatInAHat/toolfactory.git "$(FACTORY_DIR)"
	git -C "$(FACTORY_DIR)" fetch --depth 1 origin "$(TOOLFACTORY_REVISION)"
	git -C "$(FACTORY_DIR)" checkout --detach "$(TOOLFACTORY_REVISION)"
	cd "$(FACTORY_DIR)" && CI=true npx --yes pnpm@10.33.0 install --frozen-lockfile
	touch "$@"

build validate: prepare
	cd "$(FACTORY_DIR)" && node --import tsx src/toolfactory/cli.ts $@ --root "$(CURDIR)"

# Archive the generated plugin plus legal/provenance files; no runtime dependencies.
package: prepare
	rm -rf dist/release && mkdir -p dist/release
	zip -qr dist/release/papervizagent-codex-plugin.zip skills .codex-plugin .agents/plugins LICENSE NOTICE UPSTREAM.json FIDELITY.md -x '*/__pycache__/*' '*.pyc'

check: prepare
	cd "$(FACTORY_DIR)" && node --import tsx src/toolfactory/cli.ts check --root "$(CURDIR)"
	python3 -B -m unittest discover -s tests -v

test:
	python3 -B -m unittest discover -s tests -v
