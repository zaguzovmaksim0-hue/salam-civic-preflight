# Build with a compiler release pinned and verified by SHA-256.
# Runtime: no Salam toolchain, no package manager, no network access needed.
FROM debian:trixie-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl gcc libc6-dev python3 \
  && rm -rf /var/lib/apt/lists/*

ARG SALAM_VERSION=0.5.0
ARG SALAM_SHA256=8bdaeb08bde800b616520eedde4706bb621cf85bc05a8e4be9a8c0b193fcc363

WORKDIR /opt/salam
RUN set -eu; \
    curl -fLsS --retry 3 \
      "https://github.com/SalamLang/Salam/releases/download/v${SALAM_VERSION}/salam-${SALAM_VERSION}-linux-x86_64.tar.gz" \
      -o /tmp/salam.tar.gz; \
    echo "${SALAM_SHA256}  /tmp/salam.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/salam.tar.gz -C /opt/salam; \
    rm /tmp/salam.tar.gz

WORKDIR /app
COPY src/ src/
COPY tests/ tests/
COPY examples/ examples/

RUN mkdir -p .cache \
  && /opt/salam/salam-linux-x86_64/salam build src/main.salam \
       --backend=c --cc=/usr/bin/gcc --output=.cache/civic-preflight \
  && python3 tests/verify.py .cache/civic-preflight

FROM debian:trixie-slim AS runtime
COPY --from=builder /app/.cache/civic-preflight /usr/local/bin/civic-preflight
USER 65532:65532
WORKDIR /work
ENTRYPOINT ["/usr/local/bin/civic-preflight"]
CMD ["--help"]
