#!/bin/bash

python3 launcher.py
exit_status=$?
echo "exit ${exit_status}"
exit ${exit_status}
