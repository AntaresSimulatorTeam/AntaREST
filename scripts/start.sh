#!/bin/bash

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
    uvicorn antarest.wsgi:app --host 0.0.0.0 --port $((5000 + $i)) --log-level info --timeout-keep-alive 600 &
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