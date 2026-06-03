# Contributing

### Install dev requirements

Install dev requirements with `uv sync --all-extras`

### Linting and formatting

To reformat your code, use this command line: 

```shell
uv run ruff check antarest/ tests/ --fix && uv run ruff format antarest/ tests/
```

### Typechecking

To typecheck your code, use this command line: 

```shell
uv run mypy
``` 

or (`uv run mypy --install-types --non-interactive` inside the CI).

### Testing

Integration tests can take quite a while to run on your local environment.
To speed up the process, you may launch pytest with these given args 

```
uv run pytest --basetemp=/path_to_your_projects/AntaREST/target -n logical --dist=worksteal
``` 
