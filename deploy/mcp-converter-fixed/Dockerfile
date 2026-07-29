ARG BASE_IMAGE=govpress-mcp-converter:latest
FROM ${BASE_IMAGE}

ARG CONVERTER_VERSION
ARG CONVERTER_COMMIT
ARG CONVERTER_WHEEL_SHA256

COPY govpress_converter-0.4.7-py3-none-any.whl /opt/govpress-wheels/govpress_converter-0.4.7-py3-none-any.whl
RUN echo "${CONVERTER_WHEEL_SHA256}  /opt/govpress-wheels/govpress_converter-0.4.7-py3-none-any.whl" | sha256sum -c - \
    && python -m venv --system-site-packages /opt/govpress-hwpx-md-venv \
    && /opt/govpress-hwpx-md-venv/bin/python -m pip install \
        --no-cache-dir --no-deps --no-index /opt/govpress-wheels/govpress_converter-0.4.7-py3-none-any.whl \
    && python -m pip uninstall -y govpress-converter

ENV GOVPRESS_HWPX_MD_PYTHON=/opt/govpress-hwpx-md-venv/bin/python \
    GOVPRESS_HWPX_MD_EXPECTED_VERSION=${CONVERTER_VERSION} \
    GOVPRESS_HWPX_MD_WHEEL=/opt/govpress-wheels/govpress_converter-0.4.7-py3-none-any.whl \
    GOVPRESS_HWPX_MD_WHEEL_SHA256=${CONVERTER_WHEEL_SHA256} \
    PATH=/opt/govpress-hwpx-md-venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

LABEL org.opencontainers.image.version="${CONVERTER_VERSION}" \
      org.opencontainers.image.revision="${CONVERTER_COMMIT}" \
      cloud.govpress.converter.wheel-sha256="${CONVERTER_WHEEL_SHA256}"

COPY preflight.py /usr/local/libexec/govpress-converter-preflight.py
RUN /opt/govpress-hwpx-md-venv/bin/python \
      /usr/local/libexec/govpress-converter-preflight.py --check-only \
    && /opt/govpress-hwpx-md-venv/bin/python -c "import govpress_mcp.server"

ENTRYPOINT ["/opt/govpress-hwpx-md-venv/bin/python", "/usr/local/libexec/govpress-converter-preflight.py"]
