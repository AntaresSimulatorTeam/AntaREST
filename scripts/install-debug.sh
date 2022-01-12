#!/bin/bash

set -e

python3 -m venv /debug_env
source /debug_env/bin/activate
pip3 install pystack-debugger
deactivate