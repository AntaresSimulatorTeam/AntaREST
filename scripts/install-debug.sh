#!/bin/bash

set -e

python3.11 -m venv /debug_env
source /debug_env/bin/activate
pip3 install --upgrade pip && pip3 install -r /conf/requirements.txt
deactivate