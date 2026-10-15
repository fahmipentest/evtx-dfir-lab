#!/usr/bin/env bash
# setup.sh - Siapkan seluruh lab: venv Python, sampel EVTX, Chainsaw, aturan Sigma.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CHAINSAW_VER="v2.17.1"
cd "$ROOT"

echo "[1/4] Membuat virtual environment dan memasang python-evtx"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

mkdir -p samples tools output

echo "[2/4] Mengunduh sampel EVTX-ATTACK-SAMPLES"
[ -d samples/EVTX-ATTACK-SAMPLES ] || \
  git clone --depth 1 https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES.git samples/EVTX-ATTACK-SAMPLES

echo "[3/4] Mengunduh Chainsaw ${CHAINSAW_VER}"
case "$(uname -m)" in
  x86_64)  ARCH="x86_64-unknown-linux-gnu" ;;
  aarch64) ARCH="aarch64-unknown-linux-gnu" ;;
  *) echo "Arsitektur $(uname -m) tidak dikenali, unduh Chainsaw manual."; ARCH="" ;;
esac
if [ -n "$ARCH" ] && [ ! -x tools/chainsaw/chainsaw ]; then
  curl -fsSL -o tools/chainsaw.tgz \
    "https://github.com/WithSecureLabs/chainsaw/releases/download/${CHAINSAW_VER}/chainsaw_${ARCH}.tar.gz"
  tar xzf tools/chainsaw.tgz -C tools
  rm tools/chainsaw.tgz
fi

echo "[4/4] Mengunduh aturan Sigma"
[ -d tools/sigma ] || git clone --depth 1 https://github.com/SigmaHQ/sigma.git tools/sigma

echo
echo "Selesai. Aktifkan environment dengan:  source .venv/bin/activate"
