ARG VARIANT="3.10-bullseye"
FROM mcr.microsoft.com/vscode/devcontainers/python:0-${VARIANT}

ARG NODE_VERSION="lts/*"
RUN if [ "${NODE_VERSION}" != "none" ]; then su vscode -c "umask 0002 && . /usr/local/share/nvm/nvm.sh && nvm install ${NODE_VERSION} 2>&1"; fi

# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
COPY requirements.txt /tmp/pip-tmp/
RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt && rm -rf /tmp/pip-tmp

WORKDIR /app
ENV cachebust=1
RUN git clone https://github.com/entmike/feverdreams.git
WORKDIR /app/feverdreams/api