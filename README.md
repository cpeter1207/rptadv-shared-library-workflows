# rptadv-shared-library-workflows

Reusable quality and Debian 13 release jobs for the radio core, GPIO adapter,
and FFmpeg adapter. Each source repository supplies its versioned Makefile and
source-owned Dockerfile; workflows run native amd64 and arm64 jobs and preserve
production coverage requirements. Releases include Debian packages, source
archives, and SHA256SUMS and require a passing merged pull request.
