# Release coverage

ToolFactory 0.1.2 generates 18 selected surfaces from one Python runtime:
Agent Skill, Agent Plugins, Claude, Codex, Cursor, Gemini, MCP, CLI, PyPI, npm,
MCP Registry, MCPB, OpenClaw, Hermes, ClawHub, web, DSH and browser extensions.
The browser extension is a local MCP client, not a hosted inference service.

A packaged integration is not automatically an approved public store listing.
GitHub release assets contain the Python distributions, npm launcher, MCPB,
plugin bundles, OpenClaw package, web build and browser archives. PyPI is the
canonical runtime; publish it before the npm launcher is useful. Source installs
and MCPB do not require an existing PyPI package.

## Current publication status

The v0.3.0 GitHub release provides downloadable integrations independently of
registry accounts. PyPI and npm publication, ClawHub listings and browser-store
submission remain pending their publisher setup. The GitHub `pypi` environment
and Pages source are configured; the PyPI trusted-publisher record must still be
created by its account owner. No registry credential is stored in this repository.

## Registry setup

- **PyPI:** create a pending trusted publisher for project `papervizagent`,
  owner `GoatInAHat`, repository `PaperVizAgent`, workflow `release.yml`,
  environment `pypi`. Set GitHub variable `PYPI_TRUSTED_PUBLISHER=true` only
  after that record exists. No long-lived PyPI token is needed.
- **npm:** publish the first tested launcher package, configure npm's GitHub
  trusted publisher for this repository and `release.yml`, then set
  `NPM_TRUSTED_PUBLISHER=true`. npm's initial publication may require account 2FA.
- **GHCR / MCP Registry / Pages:** GitHub identity supplies workflow credentials.
  Set a newly created GHCR package public and enable Pages with source Actions.
  MCP Registry publishing waits for the package transports in server.json.
- **ClawHub:** supply `CLAWHUB_TOKEN` for skill/package publication.
- **Chrome / Firefox / Edge:** generated archives are available independently
  of store publication. Listings require the respective publisher account,
  extension ID and store credentials; `toolfactory secrets status` lists names.
- **Host directories:** installable plugin/skill artifacts do not imply approval
  into a host's curated directory. Submit after testing against that host.

The release workflow skips unconfigured registries. After completing a pending
setup, dispatch `release.yml` with the existing version tag. It uses the pinned
commit and skips already-published immutable npm versions. Do not retag releases.

## Verification

`make check`, `make validate`, and `make package` cover runtime behavior,
ToolFactory drift, upstream format validators and package creation. Inspect
wheel/sdist/MCPB contents and launch the MCPB staging directory with `uv run`
from outside the repository. Live Codex tests are recorded under `evals/`; API
provider credentials are not required for CI; provider wire tests use mocks,
while the Codex path has live end-to-end coverage.
