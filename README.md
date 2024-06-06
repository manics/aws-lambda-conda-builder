# Build custom Conda environments in a container

## Build container

`docker build -t conda-custom-envs .`

## Run container

Create a directory `$ENVDIR` containing a Conda `environment.yml`, and mount this directory to `/build` in the container:

`docker run -it --rm -v "$ENVDIR:/build" conda-custom-envs conda-env-builder environment.yml`

## Platform

Pass `--platform=linux/amd64` if you need to build a AMD64 environment on an ARM64 host.
