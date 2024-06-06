# https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-clients
FROM docker.io/condaforge/mambaforge:24.3.0-0

RUN mamba install -y -q \
    awslambdaric \
    boto3 \
    conda-pack \
    pyyaml
COPY pyproject.toml aws_conda_env_builder.py LICENSE.txt README.md /src/custom-conda-envs/
RUN pip install /src/custom-conda-envs/

COPY entrypoint.sh /user/local/bin/

WORKDIR /build

# Set runtime interface client as default command for the container runtime
ENTRYPOINT ["/user/local/bin/entrypoint.sh"]
# Pass the name of the function handler as an argument to the runtime
CMD ["aws_conda_env_builder.handler"]
