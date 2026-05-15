FROM python:3.11-slim

ARG GOVPRESS_CONVERTER_SPEC=""
ARG GOVPRESS_CONVERTER_EXTRA_INDEX_URL=""
ARG GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK="0"
ARG GOVPRESS_CONVERTER_MIN_VERSION=""
ARG GOVPRESS_HWPX_MD_SPEC=""

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

COPY requirements.txt /app/requirements.txt
COPY deploy/converter.version /tmp/govpress-converter.version
RUN pip install -r /app/requirements.txt \
    && pip install -U opendataloader-pdf \
    && echo "govpress-converter target: $(cat /tmp/govpress-converter.version)" \
    && if [ -n "$GOVPRESS_CONVERTER_SPEC" ] && [ "$GOVPRESS_CONVERTER_SPEC" != "-" ]; then pip install --upgrade --force-reinstall "$GOVPRESS_CONVERTER_SPEC"; fi \
    && HWPX_MD_INSTALL_SPEC="$GOVPRESS_HWPX_MD_SPEC" \
    && if [ -z "$HWPX_MD_INSTALL_SPEC" ] && printf '%s' "$GOVPRESS_CONVERTER_SPEC" | grep -q 'github.com/wavelen-jw/gov-md-converter.git@'; then HWPX_MD_INSTALL_SPEC="$(printf '%s' "$GOVPRESS_CONVERTER_SPEC" | sed 's#github.com/wavelen-jw/gov-md-converter.git@.*#github.com/wavelen-jw/govpress-hwpx-md.git@v0.1.1#')"; fi \
    && if [ -n "$HWPX_MD_INSTALL_SPEC" ] && [ "$HWPX_MD_INSTALL_SPEC" != "-" ]; then python -m venv /opt/govpress-hwpx-md-venv && /opt/govpress-hwpx-md-venv/bin/python -m pip install -U pip && /opt/govpress-hwpx-md-venv/bin/python -m pip install --upgrade --force-reinstall "$HWPX_MD_INSTALL_SPEC"; fi

COPY . /app

RUN if [ -n "$GOVPRESS_CONVERTER_SPEC" ] || [ "$GOVPRESS_CONVERTER_ALLOW_LOCAL_FALLBACK" = "0" ]; then \
      if [ -n "$GOVPRESS_CONVERTER_MIN_VERSION" ]; then \
        python /app/scripts/check_converter_runtime.py --require-package-backend --expected-version "$GOVPRESS_CONVERTER_MIN_VERSION"; \
      else \
        python /app/scripts/check_converter_runtime.py --require-package-backend; \
      fi; \
    fi

EXPOSE 8013

CMD ["python", "-m", "uvicorn", "server.app.main:app", "--host", "0.0.0.0", "--port", "8013"]
