#!/usr/bin/env bash
# Build the patched Main_MiSTer for the MiSTer's ARM CPU. Run inside WSL (Ubuntu) as root:
#   wsl -d Ubuntu -u root -- bash "/mnt/c/Users/joelw/Mister Guncon2/scripts/build-main-mister.sh"
#
# Fetches Main_MiSTer at the pinned commit into WSL's own filesystem (building on /mnt/c is slow), applies
# patches/*.patch in order, runs the host unit tests, then builds two binaries into <repo>/build/:
#   MiSTer_tracker_debug  tracker + GUNDBG trace logging
#   MiSTer_tracker        tracker only (what you would actually run)
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
base=13f1de93544ca2125c286ab3545f8fa63fd2d4f6
work=/root/build/Main_MiSTer
tcdir=/root/mister-toolchain
tcname=gcc-arm-10.2-2020.11-x86_64-arm-none-linux-gnueabihf
tcsha=102825ae56c9e00142d06f35d2bdd3299edb6060e84a275a25b095e66fd3fc2a   # SHA-256 of the tarball as downloaded 2026-10-15

if [ ! -x "$tcdir/$tcname/bin/arm-none-linux-gnueabihf-gcc" ]; then
	mkdir -p "$tcdir" && cd "$tcdir"
	wget -q -c "https://developer.arm.com/-/media/Files/downloads/gnu-a/10.2-2020.11/binrel/$tcname.tar.xz"
	echo "$tcsha  $tcname.tar.xz" | sha256sum -c -
	tar xf "$tcname.tar.xz" && rm "$tcname.tar.xz"
fi
export PATH="$tcdir/$tcname/bin:$PATH"

mkdir -p "$work" && cd "$work"
[ -d .git ] || { git init -q && git remote add origin https://github.com/MiSTer-devel/Main_MiSTer; }
git cat-file -e "$base^{commit}" 2>/dev/null || git fetch -q --depth 1 origin "$base"
git reset -q --hard "$base"
for p in "$repo"/patches/*.patch; do
	git -c user.name=build -c user.email=build@localhost am -q "$p"
done
git log --oneline "$base"..HEAD

g++ -std=gnu++14 -Wall -Wextra -I. test/lightgun_crt_test.cpp lightgun_crt.cpp -o /tmp/lgtest && /tmp/lgtest
g++ -std=gnu++14 -Wall -Wextra -I. test/guncal_test.cpp guncal.cpp -o /tmp/gctest && /tmp/gctest

mkdir -p "$repo/build"
rm -f bin/input.cpp.o && make GUNDBG=1 -j"$(nproc)" 2>&1 | grep -E "warning|error" || true
cp bin/MiSTer "$repo/build/MiSTer_tracker_debug"
rm -f bin/input.cpp.o && make -j"$(nproc)" 2>&1 | grep -E "warning|error" || true
cp bin/MiSTer "$repo/build/MiSTer_tracker"
md5sum "$repo"/build/MiSTer_tracker*
