# Launch mode 3: a Wavu worker in a container, built from a committed pixi.lock.
#
#   docker build -t wavu-worker .                                   # template script
#   docker build -t my-worker --build-arg SCRIPT_DIR=examples/cellpose_nuclei .
#   docker run --rm -p 8765:8765 -e WAVU_TOKEN=change-me -v "$PWD/data:/data" wavu-worker
#
# Then in Fiji: Plugins > Wavu > Connect to Running Worker, handshake file
# <host data folder>/.wavu/worker.json, host data folder <host data folder>,
# container folder /data. See README "Launch modes".
ARG PIXI_VERSION=0.78.0
FROM ghcr.io/prefix-dev/pixi:${PIXI_VERSION}

# The script folder whose environment and scripts this image serves.
ARG SCRIPT_DIR=templates/wavu-script
# hatch-vcs takes the version from git; the build context has no .git, so the
# release workflow passes the tag in.
ARG WAVU_VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${WAVU_VERSION} \
    WAVU_SCRIPT_DIR=/app/${SCRIPT_DIR} \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY templates ./templates
COPY examples ./examples
RUN cd "${WAVU_SCRIPT_DIR}" \
 && pixi install --locked \
 && pixi shell-hook -s bash > /shell-hook.sh \
 && echo 'exec "$@"' >> /shell-hook.sh \
 && rm -rf ~/.cache/rattler

VOLUME /data
EXPOSE 8765
ENTRYPOINT ["/bin/bash", "/shell-hook.sh"]
# Bind 0.0.0.0 *inside* the container only; publish the port to 127.0.0.1 on the
# host (-p 127.0.0.1:8765:8765) if other machines must not reach it.
CMD ["bash", "-c", "exec wavu-worker --script-dir \"$WAVU_SCRIPT_DIR\" --host 0.0.0.0 --port 8765 --detached --handshake-file /data/.wavu/worker.json --tmp-dir /data/.wavu-tmp"]
