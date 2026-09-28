#!/usr/bin/env bash
# Native Debian-only setup: no candidate source or static archive enters a consumer.
set -euo pipefail
manifest=$1
destination=$2
. /etc/os-release
[[ "$ID" == debian && "$VERSION_ID" == 13 ]]
export PATH="/opt/cargo/bin:/opt/rpt-advanced-quality/bin:/opt/usbradioplus-quality/bin:$PATH"
export DEBIAN_FRONTEND=noninteractive DEB_BUILD_OPTIONS=nocheck CARGO_BUILD_JOBS=2
apt-get update
apt-get install -y ca-certificates git jq build-essential devscripts equivs
# Pins are data, not shell: reject moving refs, unexpected repositories and package names.
jq -e -f "$(dirname "$0")/manifest.jq" "$manifest" >/dev/null
workspace=$(mktemp -d)
trap 'rm -rf -- "$workspace"' EXIT
architecture=$(dpkg --print-architecture)
while IFS= read -r dependency; do
  repository=$(jq -r .repository <<< "$dependency")
  revision=$(jq -r .sha <<< "$dependency")
  directory="$workspace/$repository"
  mkdir -p "$directory"
  git -C "$directory" init -q
  git -C "$directory" fetch -q --depth=1 "https://github.com/cpeter1207/$repository.git" "$revision"
  git -C "$directory" checkout -q --detach FETCH_HEAD
  [[ "$(git -C "$directory" rev-parse HEAD)" == "$revision" ]]
  (
    cd "$directory"
    mk-build-deps --install --remove --tool 'apt-get -y --no-install-recommends' debian/control
    dpkg-buildpackage -us -uc -b
  )
  packages=()
  while IFS= read -r package; do
    matches=("$workspace/${package}"_*_"$architecture".deb)
    [[ ${#matches[@]} == 1 && -f "${matches[0]}" ]]
    [[ "$(dpkg-deb -f "${matches[0]}" Package)" == "$package" ]]
    [[ "$(dpkg-deb -f "${matches[0]}" Architecture)" == "$architecture" ]]
    cp "${matches[0]}" "$destination/"
    packages+=("${matches[0]}")
  done < <(jq -r '.packages[]' <<< "$dependency")
  apt-get install --reinstall -y "${packages[@]}"
  ldconfig
done < <(jq -c '.[]' "$manifest")
