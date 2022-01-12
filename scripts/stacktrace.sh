#!/bin/bash

source /debug_env/bin/activate
echo "Printing stacktraces"
ps aux | grep python | awk '{print $2}' | xargs -I{} bash -c "echo {}; pystack --include-greenlet {}"
echo "Done"