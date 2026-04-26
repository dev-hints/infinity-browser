#!/usr/bin/env bash
# install.sh — Infinity Browser desktop integration installer
# Run this once after cloning the repository to register the app with your
# Linux desktop environment (GNOME, KDE, XFCE, etc.).
#
# Usage:
#   chmod +x install.sh
#   ./install.sh

set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DESKTOP_FILE="$HOME/.local/share/applications/infinity-browser.desktop"
ICON_DIR="$HOME/.local/share/icons/hicolor/512x512/apps"

echo "Infinity Browser — Desktop Installer"
echo "Install directory: $INSTALL_DIR"
echo ""

# ── 1. Python dependencies ────────────────────────────────────────────────────
echo "[1/4] Installing Python dependencies..."
if command -v pip3 &>/dev/null; then
    pip3 install --user -r "$INSTALL_DIR/requirements.txt" --quiet
elif command -v pip &>/dev/null; then
    pip install --user -r "$INSTALL_DIR/requirements.txt" --quiet
else
    echo "ERROR: pip not found. Please install Python pip and try again."
    exit 1
fi
echo "      Done."

# ── 2. Install icon ───────────────────────────────────────────────────────────
echo "[2/4] Installing application icon..."
mkdir -p "$ICON_DIR"
cp "$INSTALL_DIR/icons/infinity-browser.png" "$ICON_DIR/infinity-browser.png"
if command -v gtk-update-icon-cache &>/dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
fi
echo "      Done."

# ── 3. Generate and install .desktop file ────────────────────────────────────
echo "[3/4] Installing desktop entry..."
mkdir -p "$HOME/.local/share/applications"
sed "s|__INSTALL_DIR__|$INSTALL_DIR|g" \
    "$INSTALL_DIR/infinity-browser.desktop.template" \
    > "$DESKTOP_FILE"
chmod +x "$DESKTOP_FILE"
if command -v update-desktop-database &>/dev/null; then
    update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true
fi
echo "      Done."

# ── 4. Pin to GNOME dock (optional) ──────────────────────────────────────────
echo "[4/4] Checking GNOME dock..."
if command -v gsettings &>/dev/null && gsettings list-schemas 2>/dev/null | grep -q "org.gnome.shell"; then
    CURRENT=$(gsettings get org.gnome.shell favorite-apps 2>/dev/null || echo "[]")
    if echo "$CURRENT" | grep -q "infinity-browser.desktop"; then
        echo "      Already pinned to GNOME dock."
    else
        # Insert before the closing bracket
        UPDATED=$(echo "$CURRENT" | sed "s/]$/, 'infinity-browser.desktop']/")
        gsettings set org.gnome.shell favorite-apps "$UPDATED" 2>/dev/null && \
            echo "      Pinned to GNOME dock." || \
            echo "      Could not pin to dock (non-fatal)."
    fi
else
    echo "      GNOME Shell not detected — skipping dock pin."
fi

echo ""
echo "Installation complete."
echo "Infinity Browser is now available in your application launcher."
echo "To launch it manually: python3 $INSTALL_DIR/main.py"
