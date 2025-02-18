### install dev requirements

Install dev requirements with `pip install -r requirements-dev.txt`

### linting and formatting

To reformat your code, use this command line: `ruff check antarest/ tests/ --fix && ruff format antarest/ tests/`

### typechecking

To typecheck your code, use this command line: `mypy` (`mypy --install-types --non-interactive` inside the CI)

### testing

Integration tests can take quite a while to run on your local environment.
To speed up the process, you may launch pytest with these given args `--basetemp=/path_to_your_projects/AntaREST/target -n logical --dist=worksteal` 
