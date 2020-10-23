#!/bin/bash

BASEDIR=$(dirname "$0")
PROJECT_DIR=$BASEDIR/..

cd "$PROJECT_DIR" || exit

source ./venv/bin/activate
export PYTHONPATH=$PYTHONPATH:.

grn=$'\e[1;32m'
end=$'\e[0m'


printf "%s========\n" "$grn"
printf  " pytest "
printf "\n========\n %s \n" "$end"

pytest -m unit_test --no-cov --tb=line --no-header --no-summary .

printf "\n"


printf "%s======\n" "$grn"
printf " mypy"
printf "\n======\n %s \n" "$end"

mypy

printf "\n"

printf "%s=======\n" "$grn"
printf " black"
printf "\n=======\n %s" "$end"

black --diff .

printf "\n\n\n"