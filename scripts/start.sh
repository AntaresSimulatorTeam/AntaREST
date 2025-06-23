#!/bin/bash
#
# Starter script used in docker image.
#
# Usages are:
#
# 1. ./start.sh
#    Starts antares web server with gunicorn.
#    Number of workers is defined by GUNICORN_WORKERS env variable,
#    or equal to 2*cpu + 1.
#
# 2. ./start.sh <module>
#    Where module is for example "watcher".
#    Starts one of the backend services (watcher, garbage collector, ...)
#
# 3. ./start.sh --no-gunicorn
#    Starts multiple workers on different ports. You are expected to
#    configure some load balancing upstream, in that case.
#    Number of workers is defined by ANTARES_NB_WORKERS env variable,
#    or equal to 2*cpu + 1.

set -e

CUR_DIR=$(cd "$(dirname "$0")" && pwd)
BASE_DIR=$(dirname "$CUR_DIR")

min() {
    echo $(( $1 < $2 ? $1 : $2 ))
}

workers=$(min 30 ${ANTARES_NB_WORKERS:-$((2*$(nproc) + 1))}) # default (2*nproc + 1) and max is 30

# Check for --no-gunicorn or --multiple-ports argument
use_uvicorn=false
for arg in "$@"
do
    if [[ $arg == "--no-gunicorn" || $arg == "--multiple-ports" ]]; then
        use_uvicorn=true
        break
    fi
done

if [ -z "$1" ] ; then
  sh $CUR_DIR/pre-start.sh
  gunicorn --config $BASE_DIR/conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app
elif [ "$use_uvicorn" = true ]; then
  sh $CUR_DIR/pre-start.sh
  pids=() # Initialize empty array to store background process IDs
  for ((i=0; i<workers; i++))
  do
    # we still use gunicorn in that case to restart workers in case they are killed,
    # although each gunicorn instance has only one worker
    gunicorn --worker-class=uvicorn.workers.UvicornWorker \
             --bind=0.0.0.0:$((5000 + $i)) \
             --workers=1 \
             --log-level info \
             --timeout 1200 \
              antarest.wsgi:app &
    pids+=($!) # Store background process IDs
  done
  for pid in ${pids[*]};
  do
    wait $pid # Wait for each background process to finish
  done
else
  export PYTHONPATH=$BASE_DIR
  python3 $BASE_DIR/antarest/main.py -c $ANTAREST_CONF --module "$1"
fi
