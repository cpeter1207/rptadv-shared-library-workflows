FROM ghcr.io/cpeter1207/rpt-advanced-quality-debian13:latest
LABEL org.opencontainers.image.source="https://github.com/cpeter1207/rptadv-shared-library-workflows"
LABEL org.opencontainers.image.description="Native codec-provider build and validation environment"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      cmake autoconf automake libtool pkg-config libgsm1-dev libspeex-dev \
      libopus-dev libspandsp-dev libavcodec-dev libavutil-dev && \
    rm -rf /var/lib/apt/lists/*
RUN test -f /usr/include/gsm/gsm.h && \
    pkg-config --exists speex opus spandsp libavcodec libavutil && \
    cargo --version && rustc --version && cppcheck --version && \
    clang-format --version && ruff --version
WORKDIR /workspace
