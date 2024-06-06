# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-clients
FROM docker.io/condaforge/mambaforge:24.3.0-0

RUN mamba install -y -q \
    awslambdaric \
    boto3 \
    conda-pack \
    pyyaml
COPY lambda_function.py /opt/conda/lib/python3.10/site-packages/

WORKDIR /build

# Set runtime interface client as default command for the container runtime
ENTRYPOINT ["/opt/conda/bin/python", "-m", "awslambdaric"]
# Pass the name of the function handler as an argument to the runtime
CMD ["lambda_function.handler"]
