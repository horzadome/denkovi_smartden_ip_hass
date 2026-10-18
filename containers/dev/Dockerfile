# Development and test environment for the Denkovi smartDEN IP Devices integration.
# Separate from the Home Assistant runtime container, so the test dependencies stay out of the runtime.
FROM python:3.14-slim

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# uv installs the pinned test dependencies faster than pip.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /workspace

# pytest-homeassistant-custom-component pins Home Assistant 2026.10.0, pytest and the
# packages Home Assistant tests itself with. It is the whole development environment.
COPY requirements_test.txt /tmp/requirements_test.txt
RUN uv venv "$VIRTUAL_ENV" \
    && uv pip install --no-cache -r /tmp/requirements_test.txt \
    && rm /tmp/requirements_test.txt

CMD ["sleep", "infinity"]
