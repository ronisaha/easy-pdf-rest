FROM python:3.12-slim-bullseye AS builder
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes python3-venv gcc libpython3-dev gtk+3.0 && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip --no-cache-dir

FROM builder AS builder-venv
COPY requirements.txt /requirements.txt
RUN /venv/bin/pip install --disable-pip-version-check --no-cache-dir -r /requirements.txt

FROM python:slim-bullseye AS runner
RUN apt-get update && \
    apt-get install --no-install-suggests --no-install-recommends --yes gtk+3.0 curl jq \
            fontconfig \
            xfonts-75dpi \
            xfonts-base && \
        cd /tmp && \
        	curl -L -O https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6.1-2/wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
          dpkg -i wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
        rm -rf wkhtmltox_0.12.6.1-2.bullseye_amd64.deb && \
        apt-get remove -y g++ wget && \
    	apt-get autoremove --purge -y && apt-get autoclean -y && apt-get clean -y && \
      rm -rf /var/lib/apt/lists/* && \
      rm -rf /tmp/* /var/tmp/*

COPY --from=builder-venv /venv /venv
COPY weasyprint_rest /app/weasyprint_rest
ENV PRODUCTION "true"
ENV FLASK_DEBUG="false"

RUN mkdir -p /data/templates && mkdir -p /data/reports

WORKDIR /app
ENTRYPOINT ["/venv/bin/waitress-serve", "--port=5000", "--host=0.0.0.0", "--call" ,"weasyprint_rest:app"]

HEALTHCHECK --start-period=5s --interval=10s --timeout=10s --retries=5 \
    CMD curl --silent --fail --request GET http://localhost:5000/api/v1.0/health \
        | jq --exit-status '.status == "OK"' || exit 1

USER 1001
