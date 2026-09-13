# Shared library workflow rules

This companion repository owns workflow implementations for librptadvradio,
rptadv-gpio-adapter, and rptadv-ffmpeg-adapter. It contains no production code.
Validate workflow changes with Actionlint. Source pushes run only fast checks;
pull requests require documentation once, native Debian 13 amd64/arm64 builds,
tests, staged installs and packaging, plus 100% production line and branch
coverage on amd64. Releases must use a merged main revision whose pull-request
gate passed, without repeating the full gate. Never change node installations.
