# This script folder as a container: a Wavu worker plus exactly the packages in
# pixi.lock. Optional -- Fiji and napari normally start the worker themselves.
# Guide: https://oxford-zeiss-centre-of-excellence.github.io/Wavu/write/container/
#
#   docker build -t my-tool .
#   docker run --rm -p 127.0.0.1:8765:8765 -e WAVU_TOKEN=pick-one -v /my/data:/data my-tool
#
# Then in Fiji: Plugins > Wavu > Connect to Running Worker, with handshake file
# /my/data/.wavu/worker.json, host folder /my/data and container folder /data.
#
# Build it from a folder made from the template (wavu comes from GitHub). Inside
# the Wavu repository itself, use Wavu's root Dockerfile with SCRIPT_DIR instead.
ARG PIXI_VERSION=0.78.0
FROM ghcr.io/prefix-dev/pixi:${PIXI_VERSION}

# pixi fetches the wavu dependency from GitHub with git.
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
# --locked: install exactly pixi.lock (commit it); fail instead of re-solving.
RUN pixi install --locked \
 && pixi shell-hook -s bash > /shell-hook.sh \
 && echo 'exec "$@"' >> /shell-hook.sh \
 && rm -rf ~/.cache/rattler

ENV PYTHONUNBUFFERED=1
VOLUME /data
EXPOSE 8765
ENTRYPOINT ["/bin/bash", "/shell-hook.sh"]
# 0.0.0.0 only inside the container; publish to 127.0.0.1 on the host (see above)
# unless other machines should reach it. Set WAVU_TOKEN so you know the token.
CMD ["bash", "-c", "exec wavu-worker --script-dir /app --host 0.0.0.0 --port 8765 --detached --handshake-file /data/.wavu/worker.json --tmp-dir /data/.wavu-tmp"]
