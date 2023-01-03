#!/bin/bash

CURDIR=$(cd `dirname $0` && pwd)

echo "$@"
exit_status=$?
echo "exit ${exit_status}"
exit ${exit_status}
