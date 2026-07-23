# AI agents instructions for Antares Web (AntaREST)

Antares Web is a web platform (REST API + React UI) by RTE for managing
[Antares Simulator](https://antares-simulator.org) studies. It is a monorepo with a
Python/FastAPI backend in `antarest/` and a React/TypeScript frontend in `webapp/`.

## Tech stack

- **Backend**: Python 3.11, FastAPI, Pydantic v2, SQLAlchemy 2 + Alembic, Celery/Redis,
  managed with **uv** (`uv sync`, `uv run ...`).
- **Frontend**: Node 22.13, React 19, Vite, Redux Toolkit, TanStack Query/Router, MUI, vitest.
- **DB**: SQLite for local/desktop, PostgreSQL for production.

## Build, test, lint

Backend (run from repo root):

```bash
uv sync                                   # install deps (incl. dev)
uv run pytest -n auto                     # full test suite (parallel)
uv run pytest tests/study/test_x.py::test_name   # a single test
uv run ruff check antarest/ tests/ --fix  # lint + autofix
uv run ruff format antarest/ tests/       # format (line-length 120, double quotes)
uv run mypy                               # strict type check (config in pyproject.toml)
```

Frontend (run from `webapp/`):

```bash
npm install
npm run dev                               # Vite dev server (port 3000)
npm run test                              # vitest (runs with TZ=UTC)
npm run test -- src/path/File.test.tsx    # a single test file
npm run lint                              # tsc --noEmit + eslint
npm run build                             # tsc + vite build
```

Run the backend dev server:
`python antarest/main.py -c resources/application.yaml --auto-upgrade-db --no-front`

Full checks (pytest + mypy + ruff) can be run via `scripts/linter.sh`. `pre-commit` hooks
enforce mypy, ruff, and license headers.

## Architecture

**Entry points** (see `docs/architecture.md`):
- `antarest/main.py` — standalone dev server (single worker).
- `antarest/wsgi.py` — gunicorn/uvicorn app for production.
- `antarest/gui.py` — desktop application.
- `antarest/tools/admin.py` — admin CLI.
- worker services (`antarest/worker/`) — remote background jobs (e.g. unzip results).

**Module layout**: each feature package under `antarest/` (e.g. `study/`, `login/`,
`launcher/`, `matrixstore/`, `core/`) follows a consistent structure:
- `service.py` — main service / facade.
- `web.py` (or a `web/` dir of blueprints) — FastAPI REST endpoints.
- `main.py` — `build_<service>()` factory wiring dependencies.
- `model.py` — business objects, DTOs, and DB entities (may be a directory).
- `repository.py` — DB query helpers for the entities.
- `business/`, `dao/`, `adapters.py`, `utils.py` — supporting logic.

The `study/` package is the core domain (largest module): study storage lives in
`study/storage/` (raw studies, variant studies, upgraders), and DAOs in `study/dao/`.

## Key conventions

- **License headers**: every `.py`/`.ts`/`.tsx` file under `antarest/`, `tests/`, and
  `webapp/` must start with the MPL-2.0 header (see top of `antarest/main.py`). It is
  checked in pre-commit and CI via `scripts/license_checker_and_adder.py`.
- **Typing**: mypy runs in `strict` mode with `explicit-override` required; all backend
  code must be fully type-hinted.
- **Database changes**: modify SQLAlchemy models (e.g. `study/model.py`), register new
  model files in `antarest/dbmodel.py`, then generate a migration with
  `bash scripts/create_db_migration.sh "<message>"` (needs `ANTAREST_CONF` set).
  Integration tests in `tests/integration` exercise the real Alembic migration path.
- **Commits & PR titles**: Conventional Commits enforced by commitlint. Scope is
  **required** and must be lower/kebab-case, e.g. `feat(study): ...`, `fix(ui): ...`.
- **Branching**: git-flow. `dev` is the default branch; branch as `feat/...`, `fix/...`,
  `docs/...`.

## Tests

- Backend tests are in `tests/`, mirroring the `antarest/` package layout; shared
  fixtures are in `tests/conftest*.py`. `testcontainers` is used for Postgres-backed tests.
- Frontend tests are colocated as `*.test.ts(x)` and run under vitest with `TZ=UTC`.
