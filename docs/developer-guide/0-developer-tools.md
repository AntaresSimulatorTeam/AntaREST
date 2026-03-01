### install dev requirements

Install dev requirements with `uv sync --all-extras`

### linting and formatting

To reformat your code, use this command line: `uv run ruff check antarest/ tests/ --fix && uv run ruff format antarest/ tests/`

### typechecking

To typecheck your code, use this command line: `uv run mypy` (`uv run mypy --install-types --non-interactive` inside the CI)

### testing

Integration tests can take quite a while to run on your local environment.
To speed up the process, you may launch pytest with these given args `uv run pytest --basetemp=/path_to_your_projects/AntaREST/target -n logical --dist=worksteal` 
