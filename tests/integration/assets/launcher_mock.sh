#!/bin/bash

echo "$@"
exit_status=$?
echo "exit ${exit_status}"
exit ${exit_status}
