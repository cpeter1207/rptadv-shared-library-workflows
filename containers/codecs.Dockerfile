FROM ghcr.io/cpeter1207/rpt-advanced-quality-debian13:latest
LABEL org.opencontainers.image.source="https://github.com/cpeter1207/rptadv-shared-library-workflows"
LABEL org.opencontainers.image.description="Native codec-provider build and validation environment"
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      cmake autoconf automake libtool pkg-config libclang-rt-19-dev libgsm1-dev libspeex-dev \
      libopus-dev libspandsp-dev libavcodec-dev libavutil-dev && \
    rm -rf /var/lib/apt/lists/*
RUN test -f /usr/include/gsm/gsm.h && \
    pkg-config --exists speex opus spandsp libavcodec libavutil && \
    cargo --version && rustc --version && cppcheck --version && \
    clang-format --version && ruff --version
RUN printf 'int main(void) { return 0; }\n' | \
      clang -x c - -fprofile-instr-generate -fcoverage-mapping -o /tmp/codec-coverage-smoke && \
    LLVM_PROFILE_FILE=/tmp/codec-coverage-smoke.profraw /tmp/codec-coverage-smoke && \
    test -s /tmp/codec-coverage-smoke.profraw && \
    rm /tmp/codec-coverage-smoke /tmp/codec-coverage-smoke.profraw
COPY codec-bootstrap/packaging/external /opt/codec-bootstrap/packaging/external
COPY codec-bootstrap/dependencies/codecs.json /opt/codec-bootstrap/dependencies/codecs.json
COPY codec-bootstrap/include/rptadv_codec.h /usr/include/rptadv-codec/rptadv_codec.h
COPY codec-bootstrap/include /opt/codec-bootstrap/include
COPY codec-bootstrap/Cargo.toml codec-bootstrap/Cargo.lock codec-bootstrap/Makefile /opt/codec-bootstrap/
COPY codec-bootstrap/rust /opt/codec-bootstrap/rust
COPY codec-bootstrap/tests/abi_header_smoke.c /opt/codec-bootstrap/tests/abi_header_smoke.c
COPY codec-bootstrap/debian /opt/codec-bootstrap/debian
COPY codec-bootstrap/rptadv_codec.pc.in /opt/codec-bootstrap/rptadv_codec.pc.in
ENV RPTADV_CODEC_SOURCE_CACHE=/opt/rptadv-codec-source-cache
ENV RPTADV_CODEC_BACKEND_LIBDIR=/opt/rptadv-codec-backends/lib
ENV RPTADV_CODEC_DIR=/opt/rptadv-codec-providers/lib
ENV LD_LIBRARY_PATH=/opt/rptadv-codec-providers/lib:/opt/rptadv-codec-backends/lib
RUN set -eu; for backend in bcg729 ilbc dialogic; do \
      python3 /opt/codec-bootstrap/packaging/external/build.py "$backend" \
        --prefix /opt/rptadv-codec-backends; \
    done && \
    test -f "$RPTADV_CODEC_BACKEND_LIBDIR/librptadv_bcg729_gpl2.so.0" && \
    test -f "$RPTADV_CODEC_BACKEND_LIBDIR/librptadv_ilbc2.so.2" && \
    test -f "$RPTADV_CODEC_BACKEND_LIBDIR/librptadv_dialogic.so.1" && \
    make -C /opt/codec-bootstrap all abi-check && \
    mkdir -p "$RPTADV_CODEC_DIR" && \
    cp -a /opt/codec-bootstrap/build/librptadv_codec_*.so* "$RPTADV_CODEC_DIR/" && \
    python3 -c 'import ctypes, glob, os; paths = glob.glob(os.environ["RPTADV_CODEC_DIR"] + "/*.so.1"); assert len(paths) == 10; [ctypes.CDLL(path) for path in paths]' && \
    (cd /opt/codec-bootstrap && DEB_BUILD_OPTIONS=nocheck dpkg-buildpackage -us -uc -b) && \
    dpkg -i /opt/librptadv-*.deb && \
    test "$(dpkg-query -W -f='${db:Status-Status}' librptadv-codec-dev)" = installed && \
    rm -rf /opt/codec-bootstrap && \
    rm -f /opt/librptadv-*.deb /opt/rptadv-codec-adapters_*.buildinfo /opt/rptadv-codec-adapters_*.changes
WORKDIR /workspace
