#!/usr/bin/env bash
# Re-creates the read-only upstream reference material used for this project.
# Nothing here is tracked in git; everything is pinned to the commits that were
# read when the notes in README.md were written. Needs git and an authenticated gh.
set -euo pipefail
cd "$(dirname "$0")/.."

clone() { # dir url sha
	[ -d "$1/.git" ] || git clone --filter=blob:none "$2" "$1"
	git -C "$1" checkout --quiet "$3"
}
raw() { # repo path sha out
	mkdir -p "$(dirname "$4")"
	gh api -H "Accept: application/vnd.github.raw" "repos/$1/contents/$2?ref=$3" > "$4"
}

clone Main_MiSTer     https://github.com/MiSTer-devel/Main_MiSTer           13f1de93544ca2125c286ab3545f8fa63fd2d4f6
clone GunCon2-MiSTer  https://github.com/NolanNicholson/GunCon2-MiSTer      d269e99a5819c02b5eb113e1a448fd14c60b59d6

raw MiSTer-devel/Linux-Kernel_MiSTer drivers/hid/hid-guncon2.c b5b122995780200ad615c91f5fd4b92d3e2483b2 Linux-Kernel_MiSTer-guncon2/hid-guncon2.c

raw MiSTer-devel/NES_MiSTer       rtl/zapper.sv         49a0a662e244469ca77b2155746a066df704ffae core-refs/NES_zapper.sv
raw MiSTer-devel/SNES_MiSTer      rtl/lightgun.sv       23026830ff8108fda0f32c0616296845f586b8ce core-refs/SNES_lightgun.sv
raw MiSTer-devel/MegaDrive_MiSTer rtl/pad_io.sv         becbdee78c48e6eb536871cd03c869f43d7afa4d core-refs/MD_pad_io.sv
raw MiSTer-devel/PSX_MiSTer       rtl/joypad.vhd        cd17b5a0ad261005c321d9d5ba41b8dbe313a7d3 core-refs/PSX_joypad.vhd
raw MiSTer-devel/PSX_MiSTer       rtl/psx_top.vhd       cd17b5a0ad261005c321d9d5ba41b8dbe313a7d3 core-refs/psx_top.vhd
raw MiSTer-devel/PSX_MiSTer       PSX.sv                cd17b5a0ad261005c321d9d5ba41b8dbe313a7d3 core-refs/PSX.sv
raw MiSTer-devel/Template_MiSTer  sys/hps_io.sv         9c8eadb40067c8ce3aef90899844f62d688ac73a core-refs/hps_io.sv
raw PCSX2/pcsx2 pcsx2/USB/usb-lightgun/guncon2.cpp      685637d30b5eaa8e5d7a587673a17577a92dcb88 core-refs/pcsx2_guncon2.cpp

echo "reference material in place"
