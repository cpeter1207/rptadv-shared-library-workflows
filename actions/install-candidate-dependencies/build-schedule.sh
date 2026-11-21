#!/usr/bin/env bash
# The pinned recurrence provider uses 1.93.0 for its Debian build only.
set -euo pipefail
case "$1" in
  amd64) target=x86_64-unknown-linux-gnu ;;
  arm64) target=aarch64-unknown-linux-gnu ;;
  *) echo "unsupported schedule architecture: $1" >&2; exit 1 ;;
esac
checksums=$(realpath "$(dirname "$0")/rust-1.93.0-$1.sha256")
temporary=$(mktemp -d "$2/schedule-rust.XXXXXXXX")
prefix="$temporary/toolchain"
trap 'rm -rf -- "$temporary"' EXIT
(
  cd "$temporary"
  while read -r digest archive; do
    curl --proto '=https' --tlsv1.2 --fail --silent --show-error --retry 3 \
      --output "$archive" "https://static.rust-lang.org/dist/2026-01-22/$archive"
    printf '%s  %s\n' "$digest" "$archive" | sha256sum --strict --check -
    directory=${archive%.tar.xz}
    tar -xJf "$archive"
    bash "$directory/install.sh" --prefix="$prefix" --disable-ldconfig
    rm -rf -- "$archive" "$directory"
  done < "$checksums"
)
export PATH="$prefix/bin:$PATH" CARGO_HOME="$temporary/cargo"
export RUSTC="$prefix/bin/rustc" CARGO="$prefix/bin/cargo"
rust_version=$("$RUSTC" -vV)
cargo_version=$("$CARGO" --version)
printf '%s\n%s\n' "$rust_version" "$cargo_version"
grep -Fxq 'release: 1.93.0' <<< "$rust_version"
grep -Fxq "host: $target" <<< "$rust_version"
[[ "$cargo_version" == 'cargo 1.93.0 '* ]]

# These are the pinned source's non-Rust Build-Depends. Recheck the entire
# original control file and accept only its exact compiler alternatives.
apt-get -y --no-install-recommends satisfy 'debhelper-compat (= 13), pkg-config'
flags=()
if diagnostic=$(LC_ALL=C dpkg-checkbuilddeps 2>&1); then
  :
else
  status=$?
  printf '%s\n' "$diagnostic" >&2
  [[ "$status" == 1 ]]
  cargo_dep='cargo (>= 1.93) | cargo-web (>= 1.93)'
  rustc_dep='rustc (>= 1.93) | rustc-web (>= 1.93)'
  case "$diagnostic" in
    "dpkg-checkbuilddeps: error: unmet build dependencies: $cargo_dep" | \
    "dpkg-checkbuilddeps: error: unmet build dependencies: $rustc_dep" | \
    "dpkg-checkbuilddeps: error: unmet build dependencies: $cargo_dep $rustc_dep") flags=(-d) ;;
    *) exit 1 ;;
  esac
fi
dpkg-buildpackage -us -uc -b "${flags[@]}"
