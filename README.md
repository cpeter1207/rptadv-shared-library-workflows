# rptadv-shared-library-workflows

Reusable quality and Debian 13 release jobs for the radio core, GPIO adapter,
FFmpeg adapter, and RNNoise adapter. Each source repository supplies its versioned Makefile and
source-owned Dockerfile; workflows run native amd64 and arm64 jobs and preserve
production coverage requirements. Releases include Debian packages, source
archives, and SHA256SUMS and require a passing merged pull request.

The RNNoise caller selects `release-packages` to include the official RNNoise
companion packages already built by its quality image. Other callers use the
default `debian-package-check` target. The native test launcher may expose the
Docker socket for source-owned autopkgtest checks.
