FROM python:3.11-slim

ARG GOVPRESS_CONVERTER_SPEC=""
ARG GOVPRESS_CONVERTER_INSTALL_SPEC=""
ARG GOVPRESS_CONVERTER_EXTRA_INDEX_URL=""
ARG GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK="0"
ARG GOVPRESS_CONVERTER_MIN_VERSION=""
ARG GOVPRESS_HWPX_MD_SPEC=""
ARG RHWP_VERSION="0.8.4"
ARG RHWP_LINUX_X86_64_SHA256="d2f015447147a840b3a587e8e9bedd75973fb2e0a60eac37b08cad9e34cdac54"
ARG GOVPRESS_HWPX_MD_INSTALL_SPEC=""

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_EXTRA_INDEX_URL=${GOVPRESS_CONVERTER_EXTRA_INDEX_URL} \
    GOVPRESS_HWPX_MD_PYTHON=/opt/govpress-hwpx-md-venv/bin/python \
    GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK=${GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK}

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends default-jre-headless curl git \
    && rm -rf /var/lib/apt/lists/*

COPY .deploy-artifacts /tmp/deploy-artifacts
RUN set -eux; \
    archive="/tmp/rhwp-v${RHWP_VERSION}-linux-x86_64.tar.gz"; \
    offline_archive="/tmp/deploy-artifacts/rhwp-v${RHWP_VERSION}-linux-x86_64.tar.gz"; \
    if [ -f "$offline_archive" ]; then cp "$offline_archive" "$archive"; else curl -fsSL "https://github.com/edwardkim/rhwp/releases/download/v${RHWP_VERSION}/rhwp-v${RHWP_VERSION}-linux-x86_64.tar.gz" -o "$archive"; fi; \
    echo "${RHWP_LINUX_X86_64_SHA256}  $archive" | sha256sum -c -; \
    tar -xzf "$archive" -C /tmp; \
    install -m 0755 /tmp/rhwp/rhwp /usr/local/bin/rhwp; \
    rm -rf "$archive" /tmp/rhwp; \
    rhwp --version

COPY requirements.txt /app/requirements.txt
COPY deploy/converter.version /tmp/govpress-converter.version
RUN pip install -r /app/requirements.txt \
    && pip install -U opendataloader-pdf \
    && echo "govpress-converter target: $(cat /tmp/govpress-converter.version)" \
    && CONVERTER_INSTALL_SPEC="${GOVPRESS_CONVERTER_INSTALL_SPEC:-$GOVPRESS_CONVERTER_SPEC}" \
    && if [ -n "$CONVERTER_INSTALL_SPEC" ] && [ "$CONVERTER_INSTALL_SPEC" != "-" ]; then pip install --upgrade --force-reinstall "$CONVERTER_INSTALL_SPEC"; fi \
    && HWPX_MD_INSTALL_SPEC="${GOVPRESS_HWPX_MD_INSTALL_SPEC:-$GOVPRESS_HWPX_MD_SPEC}" \
    && if [ -z "$HWPX_MD_INSTALL_SPEC" ] && printf '%s' "$GOVPRESS_CONVERTER_SPEC" | grep -q 'github.com/wavelen-jw/gov-md-converter.git@'; then HWPX_MD_INSTALL_SPEC="$(printf '%s' "$GOVPRESS_CONVERTER_SPEC" | sed 's#github.com/wavelen-jw/gov-md-converter.git@#github.com/wavelen-jw/govpress-hwpx-md.git@#')"; fi \
    && if [ -n "$HWPX_MD_INSTALL_SPEC" ] && [ "$HWPX_MD_INSTALL_SPEC" != "-" ]; then python -m venv /opt/govpress-hwpx-md-venv && /opt/govpress-hwpx-md-venv/bin/python -m pip install -U pip && /opt/govpress-hwpx-md-venv/bin/python -m pip install --upgrade --force-reinstall "$HWPX_MD_INSTALL_SPEC" && /opt/govpress-hwpx-md-venv/bin/python -c "import govpress_converter; print(getattr(govpress_converter, '__version__', ''))"; fi

COPY . /app

RUN if { [ -n "$GOVPRESS_CONVERTER_SPEC" ] && [ "$GOVPRESS_CONVERTER_SPEC" != "-" ]; } || [ "$GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" = "0" ]; then \
      if [ -n "$GOVPRESS_CONVERTER_MIN_VERSION" ]; then \
        python /app/scripts/check_converter_runtime.py --require-package-backend --expected-version "$GOVPRESS_CONVERTER_MIN_VERSION"; \
      else \
        python /app/scripts/check_converter_runtime.py --require-package-backend; \
      fi; \
    fi

EXPOSE 8013

CMD ["python", "-m", "uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8013"]
