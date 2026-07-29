# Fixed MCP converter image

The MCP converter must use the same immutable `govpress-hwpx-md` wheel on
serverN, serverW, and serverV. The release contract for v0.4.7 is:

- source commit: `c2960871aa22e3d369dc10f05558767d8f272259`
- wheel SHA-256: `2ea69649191968782af742461c9b7480e4a294d426c512c76d37656f4a66af24`
- image tag: `govpress-mcp-converter:0.4.7-c2960871`
- runtime Python: `/opt/govpress-hwpx-md-venv/bin/python`
- no startup-time package installation

Build the wheel from a clean checkout of the release commit, transfer that
wheel and this service revision to the build host, and run:

```bash
CONVERTER_IMAGE_TAG=govpress-mcp-converter:0.4.7-c2960871 \
deploy/mcp-converter-fixed/build.sh \
  /path/to/govpress_converter-0.4.7-py3-none-any.whl \
  govpress-mcp-converter:latest
```

The build verifies wheel metadata and SHA-256, installs it at image build time,
removes the ambiguous system converter package, and records the release
version, commit, and wheel SHA-256 as image labels. The image entrypoint checks
the configured Python path, distribution version, module version, and CLI
version before starting any command.

## Rollout

Transfer the exact tagged image to each server rather than rebuilding it
independently. Before rollout, record the current MCP container image ID.

```bash
docker inspect -f '{{.Image}}' govpress-mcp-server-1
docker save govpress-mcp-converter:0.4.7-c2960871 | gzip -1 \
  > govpress-mcp-converter-0.4.7-c2960871.tar.gz
sha256sum govpress-mcp-converter-0.4.7-c2960871.tar.gz
```

After loading the same archive on serverN, serverW, and serverV:

```bash
export GOVPRESS_MCP_CONVERTER_IMAGE=govpress-mcp-converter:0.4.7-c2960871
docker compose \
  -f docker-compose.yml \
  -f docker-compose.converter-v047.yml \
  config
scripts/preflight-mcp-converter.sh candidate-container-name
```

Only after the candidate conversion test passes may an operator recreate the
MCP service with both compose files. The converter preflight must run before
each archive conversion and fail closed on any mismatch.

## Rollback

Keep the previous image by immutable image ID. To roll back, set
`GOVPRESS_MCP_CONVERTER_IMAGE` to that recorded ID, recreate only the MCP
service with the same compose override, and run the preflight expected by that
release. SQLite, Qdrant, raw HWPX, and Markdown volumes are not replaced.
