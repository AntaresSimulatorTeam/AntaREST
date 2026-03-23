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

if [[ -v PROMETHEUS_MULTIPROC_DIR ]]; then
  rm -f ${PROMETHEUS_MULTIPROC_DIR}/*.db
  mkdir -p ${PROMETHEUS_MULTIPROC_DIR}
  echo "Concatenating metrics into ${PROMETHEUS_MULTIPROC_DIR}"
fi

if [ -z "$1" ] ; then
  gunicorn --config $BASE_DIR/conf/gunicorn.py --worker-class=uvicorn.workers.UvicornWorker antarest.wsgi:app
elif [ "$use_uvicorn" = true ]; then
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
             --config $BASE_DIR/conf/gunicorn-single.py \
            antarest.wsgi:app &
    pids+=($!) # Store background process IDs
  done
  for pid in ${pids[*]};
  do
    wait $pid # Wait for each background process to finish
  done
else
  export PYTHONPATH=$BASE_DIR

  # Check if module is celery-related
  case "$1" in
    celery-beat)
      echo "Starting Celery Beat scheduler..."
      exec celery -A antarest.maintenance.app:celery_app beat \
        --loglevel=info \
        --pidfile=/tmp/celerybeat.pid
      ;;
    celery-worker)
      echo "Starting Celery Worker..."
      CONCURRENCY="${CELERY_CONCURRENCY:-1}"
      POOL="${CELERY_POOL:-solo}"
      exec celery -A antarest.maintenance.app:celery_app worker \
        --loglevel=info \
        --concurrency=$CONCURRENCY \
        --pool=$POOL \
        --queues=maintenance \
        --max-tasks-per-child=100
      ;;
    *)
      # Default: run antarest module (watcher, auto_archiver, etc.)
      python $BASE_DIR/antarest/main.py -c $ANTAREST_CONF --module "$1"
      ;;
  esac
fi
