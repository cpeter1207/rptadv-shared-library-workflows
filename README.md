# rptadv-shared-library-workflows

Reusable quality and Debian 13 release jobs for the radio core, GPIO adapter,
FFmpeg adapter, RNNoise adapter, and IAX2 library. Each source repository
supplies its versioned Makefile and source-owned Dockerfile; workflows run native
amd64 and arm64 jobs and preserve
production coverage requirements. Releases include Debian packages, source
archives, and SHA256SUMS and require a passing merged pull request.

The RNNoise caller selects `release-packages` to include the official RNNoise
companion packages already built by its quality image. Other callers use the
default `debian-package-check` target. The native test launcher may expose the
Docker socket for source-owned autopkgtest checks.

New functional-library callers pass `APT_INDEX_DISPATCH_TOKEN` to the reusable
release workflow. After GitHub publishes its Debian 13 release assets, the
workflow dispatches that repository and tag to USBRadioPlus's signed package
index. Existing callers without the secret keep their current release behavior.
The token needs only `Contents: write` on `cpeter1207/USBRadioPlus`.
When the secret is absent, the release reports that index publication was skipped.

The reusable `documentation.yml(code_ref)` publishes source-owned `make docs`
output to the source repository's GitHub Pages site after confirming that the
revision is merged into `main` and its pull-request quality gate passed. Thin
main-push callers grant `contents: read`, `pull-requests: read`, `checks: read`,
`pages: write`, and `id-token: write`. Documentation publication does not repeat
the full quality gate.

## Unreleased ABI validation

`actions/install-candidate-dependencies` reads an optional ordered
`.github/dependencies.json` in the calling source checkout. Each entry names a
project repository, an exact 40-character commit SHA, and its runtime/development
Debian packages. Dependencies are built and installed in list order on native
Debian 13. Use this only when a consumer needs an unreleased shared ABI; ordinary
released dependencies continue to use verified release artifacts.

Candidate sources stay in disposable build directories. Consumers link the
resulting shared objects, never a copied source or static implementation. Explicit
reinstallation prevents an older package with the same version from satisfying
the check accidentally. This action does not tag or publish a release.
