FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ripgrep \
    jq \
    tree \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash agent \
    && mkdir -p /workspace \
    && chown -R agent:agent /workspace

USER agent
WORKDIR /workspace

CMD ["sleep", "infinity"]
