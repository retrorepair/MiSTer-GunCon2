#!/usr/bin/env bash
# Build the GunCal FPGA core with Quartus Lite 17.0 (Windows install), from Git Bash:
#   bash scripts/build-guncal.sh            full compile (about 20 minutes)
#   bash scripts/build-guncal.sh --map      synthesis only (a few minutes): catches HDL errors early
# Output: build/GunCal.rbf
set -euo pipefail

repo=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
q="${QUARTUS_BIN:-C:/intelFPGA_lite/17.0/quartus/bin64}"
tpl=9c8eadb40067c8ce3aef90899844f62d688ac73a      # Template_MiSTer commit the framework (sys/) comes from
work="$repo/build/GunCal"

[ -d "$repo/build/Template_MiSTer/.git" ] || git clone -q https://github.com/MiSTer-devel/Template_MiSTer "$repo/build/Template_MiSTer"
git -C "$repo/build/Template_MiSTer" checkout -q "$tpl"

python -I "$repo/cores/GunCal/tools/gen_font.py"
python -I "$repo/cores/GunCal/tools/gen_text.py"

rm -rf "$work" && mkdir -p "$work"
cp -r "$repo/build/Template_MiSTer/sys" "$work/sys"
cp -r "$repo/cores/GunCal/"* "$work/"
rm -rf "$work/tools"

cd "$work"
if [ "${1:-}" = "--map" ]; then
	# the full flow creates build_id.v in a pre-flow script; do the same by hand for a synthesis-only run
	printf '`define BUILD_DATE "%s"' "$(date +%y%m%d)" > build_id.v
	"$q/quartus_map.exe" GunCal --read_settings_files=on 2>&1 | tail -60
else
	"$q/quartus_sh.exe" --flow compile GunCal > "$repo/build/guncal_compile.log" 2>&1 || { tail -60 "$repo/build/guncal_compile.log"; exit 1; }
	cp output_files/GunCal.rbf "$repo/build/GunCal.rbf"
	ls -l "$repo/build/GunCal.rbf"
fi
