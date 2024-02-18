FROM python:3.12-bullseye AS builder
RUN apt-get update && apt-get upgrade -y &&  apt-get dist-upgrade -y
RUN apt-get install -y --no-install-recommends --yes  \
                    python3-venv  \
                    gcc  \
                    libpython3-dev  \
                    fontconfig \
                     xfonts-75dpi \
                     xfonts-base && \
    cd /tmp && \
            	curl -L -O https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
              dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
            rm -rf wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip --no-cache-dir

COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install --no-cache-dir -r /requirements.txt

RUN /venv/bin/pip install pylint flake8 bandit
ENV PATH="/venv/bin:${PATH}"

COPY . /app
WORKDIR /app

ARG ENABLE_BUILD_IMAGE_UPDATE=false
ARG ENABLE_BUILD_TEST=false
ARG ENABLE_BUILD_LINT=false

RUN if [ "${ENABLE_BUILD_TEST}" != "false" ] && [ "${ENABLE_BUILD_IMAGE_UPDATE}" != "true" ]; then make test; else echo "Skip test"; fi
RUN if [ "${ENABLE_BUILD_LINT}" != "false" ]; then make lint; else echo "Skip lint"; fi

RUN mkdir -p /data/templates && mkdir -p /data/reports

ENV ENABLE_BUILD_IMAGE_UPDATE=${ENABLE_BUILD_IMAGE_UPDATE}
ENV ENABLE_DEBUG_MODE=true
ENV ENABLE_RUNTIME_TEST_ONLY=false
ENV PATH="/venv/bin:${PATH}"

WORKDIR /app
ENTRYPOINT ["/app/run-dev.sh"]

LABEL name={NAME}
LABEL version={VERSION}
