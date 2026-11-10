# syntax=docker/dockerfile:1.7

# Esta receta está fijada para la plataforma arm64 utilizada en la validación.
FROM --platform=linux/arm64 ghcr.io/astral-sh/uv:python3.12-bookworm-slim@sha256:a2e8b64aed3382a20c03fc6f1e03fe95fb312425e071ad27d7936a0f02c3e497 AS uv
FROM --platform=linux/arm64 jenkins/jenkins:2.541.3-jdk21@sha256:0c84df82ef6fa400a8128b0b6f80bfd2d99f89ee571421103d818b40fbf1c483

ARG DOCKER_CLI_VERSION=5:29.9.2-1~debian.13~trixie
ARG DOCKER_COMPOSE_VERSION=5.7.0-1~debian.13~trixie

USER root

ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python \
    PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright

COPY --from=uv /usr/local/bin/uv /usr/local/bin/uv
COPY infra/jenkins/plugins.txt /opt/jenkins/plugins.txt
COPY requirements-ci.txt requirements-e2e.txt /opt/deps/

RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends ca-certificates curl gnupg; \
    install -m 0755 -d /etc/apt/keyrings; \
    curl -fsSL https://download.docker.com/linux/debian/gpg \
        -o /etc/apt/keyrings/docker.asc; \
    chmod a+r /etc/apt/keyrings/docker.asc; \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo \"$VERSION_CODENAME\") stable" \
        > /etc/apt/sources.list.d/docker.list; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
        docker-ce-cli="$DOCKER_CLI_VERSION" \
        docker-compose-plugin="$DOCKER_COMPOSE_VERSION" \
        libasound2 \
        libatk1.0-0t64 \
        libavcodec61 \
        libcairo-gobject2 \
        libcairo2 \
        libdbus-1-3 \
        libdbus-glib-1-2 \
        libfontconfig1 \
        libfreetype6 \
        libgdk-pixbuf-2.0-0 \
        libglib2.0-0t64 \
        libgtk-3-0t64 \
        libharfbuzz0b \
        libpango-1.0-0 \
        libpangocairo-1.0-0 \
        libx11-6 \
        libx11-xcb1 \
        libxcb-shm0 \
        libxcb1 \
        libxcomposite1 \
        libxcursor1 \
        libxdamage1 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxrandr2 \
        libxrender1 \
        libxtst6; \
    rm -rf /var/lib/apt/lists/*; \
    uv python install 3.12.12; \
    uv venv --python 3.12 /opt/jenkins-venv; \
    uv pip sync --python /opt/jenkins-venv/bin/python /opt/deps/requirements-ci.txt; \
    uv pip install --python /opt/jenkins-venv/bin/python --require-hashes \
        -r /opt/deps/requirements-e2e.txt; \
    mkdir -p "$PLAYWRIGHT_BROWSERS_PATH"; \
    /opt/jenkins-venv/bin/python -m playwright install firefox; \
    jenkins-plugin-cli --plugin-file /opt/jenkins/plugins.txt; \
    chown -R jenkins:jenkins /opt/jenkins-venv "$PLAYWRIGHT_BROWSERS_PATH"; \
    chmod -R a+rX /opt/uv-python /opt/jenkins-venv "$PLAYWRIGHT_BROWSERS_PATH"; \
    rm -rf /opt/deps /root/.cache/uv

ENV PATH="/opt/jenkins-venv/bin:/usr/local/bin:${PATH}"

USER jenkins
