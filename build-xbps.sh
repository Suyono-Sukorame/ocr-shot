#!/usr/bin/env bash
# build-xbps.sh - Helper script to build ocr-shot XBPS package using void-packages (xbps-src)

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VOID_PACKAGES_DIR="${1:-$HOME/void-packages}"

if [ ! -d "$VOID_PACKAGES_DIR" ] || [ ! -f "$VOID_PACKAGES_DIR/xbps-src" ]; then
    echo "❌ Error: void-packages repository not found at '$VOID_PACKAGES_DIR'."
    echo "Usage: $0 [/path/to/void-packages]"
    exit 1
fi

echo "==> Setting up ocr-shot package template in void-packages..."
mkdir -p "$VOID_PACKAGES_DIR/srcpkgs/ocr-shot"
cp -v "$SCRIPT_DIR/xbps/template" "$VOID_PACKAGES_DIR/srcpkgs/ocr-shot/template"

echo "==> Building ocr-shot XBPS package..."
cd "$VOID_PACKAGES_DIR"
./xbps-src pkg ocr-shot

echo ""
echo "✅ Build completed successfully!"
echo "To install the package on Void Linux, run:"
echo "  sudo xbps-install --repository hostdir/binpkgs ocr-shot"
