#!/bin/sh
set -e

#entrypoint.sh
if [ "$1" = 'default' ]; then
    # do the container default
    echo "Using Default Command"
    exec /venv/bin/python --version
else
    echo "Executing User Supplied Command"
    exec "$@"
fi
