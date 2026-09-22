#!/bin/bash

BASE_DIR=$(dirname "$0")
PROJECT_DIR=$BASE_DIR/..

cd "$PROJECT_DIR" || exit

export PYTHONPATH=$PYTHONPATH:.

grn=$'\e[1;32m'
end=$'\e[0m'


printf "%s========\n" "$grn"
printf  " pytest "
printf "\n========\n %s \n" "$end"

uv run pytest -m unit_test --no-cov --tb=line --no-header --no-summary .

printf "\n"


printf "%s======\n" "$grn"
printf " mypy"
printf "\n======\n %s \n" "$end"

uv run mypy

printf "\n"

printf "%s======\n" "$grn"
printf " ruff"
printf "\n======\n %s" "$end"

uv run ruff format --diff antarest
uv run ruff check antarest

printf "\n\n\n"
