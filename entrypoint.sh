#!/bin/sh
set -eu

# https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html#configuration-envvars-runtime
if [ -n "${AWS_EXECUTION_ENV:-}" ]; then
  exec /opt/conda/bin/python -m awslambdaric "$@"
else
  exec "$@"
fi
