#!/bin/bash

set -e

python3 -m venv /debug_env
source /debug_env/bin/activate
pip install --upgrade pip && pip install -r /conf/requirements.txt
deactivate