# Agent Hub Platform

A small, config-driven Q&A agent platform for a personal learning project.
Python package: `agent_hub`. CLI: `agent-hub`. All example data is fictional.

Phase 0 includes the backend and React scaffold, locked tooling, and offline smoke
tests. No agents are bundled. Config loading, models, tools, SQLite, streaming,
tracing, and the complete chat UI arrive in subsequent reviewable phases.

## Quickstart

Install Python 3.12, uv, Node.js 20+, pnpm 10, and make. No keys or Docker required.

```sh
make setup
make lint typecheck test
make web-build
make dev
# In another terminal:
make web-dev
```

Open the Vite URL (normally http://127.0.0.1:5173). The API shell runs on
http://127.0.0.1:8080; `/docs` shows its API documentation. Vite proxies `/api`
and `/health`; these application endpoints arrive in Phase 5.

## Commands

| Command | Phase 0 behavior |
| --- | --- |
| `make setup` | Install both locked environments |
| `make dev` | Run the backend shell with reload |
| `make web-dev` | Run Vite |
| `make lint` | Ruff, ESLint, and formatting checks |
| `make typecheck` | Strict mypy on core and strict TypeScript |
| `make test` | Offline pytest and Vitest smoke tests |
| `make web-build` | Typecheck and build the web app |
| `make run` | Build the web app and start the API; static serving arrives in Phase 8 |
| `make e2e` | Playwright scaffold smoke with the offline backend running |
| `make validate` | Reserved for Phase 1; currently exits 2 with an explanation |
| `make hooks` | Install local pre-commit hooks |

For e2e, install Chromium and its Linux libraries once:
`pnpm --dir web exec playwright install --with-deps chromium`.
CI installs browser OS dependencies and runs all checks without secrets.
Dependencies need network access during setup; tests use only local resources.

## Configuration and project layout

`.env.example` documents planned settings with every variable commented out.
No environment variables are required for the scaffold. Settings loading arrives
in Phase 1. Runtime dependencies are added and locked when their phase begins.

`agent_hub/agents/` and `docs/` contain only `.gitkeep`. Future test agents belong
in `tests/fixtures/agents/`, not the application agents directory. Reserved Python
modules mark the requested extension points; they do not implement runtime behavior.
The agent.yaml quick reference will arrive alongside its validation in Phase 1.

The final app will default to an offline model, fake search in offline mode, and
SQLite at `./data/agent_hub.db`. Optional tracing will default to off. Production
static serving, full chat e2e, and the 85% core coverage requirement are completed
in later phases; Phase 0 does not claim runtime coverage from placeholder modules.
