#!/bin/bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
BIN="$DIR/EchecsP2P"
ICON="$DIR/icon.png"

# Ensure executable permissions
chmod +x "$BIN" 2>/dev/null || true
if [ -f "$DIR/stockfish_bin" ]; then
    chmod +x "$DIR/stockfish_bin" 2>/dev/null || true
fi

echo "=========================================================="
echo "    Installation d'Échecs P2P Pro (Édition Stockfish 19)   "
echo "=========================================================="
echo "Dossier du jeu : $DIR"

# 1. Create Desktop Entry in ~/.local/share/applications (Standard Linux App Menu)
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/echecs-p2p.desktop" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Échecs P2P Pro
GenericName=Jeu d'échecs
Comment=Jeu d'échecs P2P LAN sans configuration et IA Stockfish 19
Exec="$BIN"
Icon=$ICON
Terminal=false
Categories=Game;BoardGame;
Keywords=chess;echecs;stockfish;p2p;
Path=$DIR
EOF

chmod +x "$DESKTOP_DIR/echecs-p2p.desktop"

# 2. If Desktop directory exists (Bureau or Desktop), create desktop shortcut too
DESKTOP_SHORTCUT=""
if [ -d "$HOME/Bureau" ]; then
    DESKTOP_SHORTCUT="$HOME/Bureau/echecs-p2p.desktop"
elif [ -d "$HOME/Desktop" ]; then
    DESKTOP_SHORTCUT="$HOME/Desktop/echecs-p2p.desktop"
fi

if [ -n "$DESKTOP_SHORTCUT" ]; then
    cp "$DESKTOP_DIR/echecs-p2p.desktop" "$DESKTOP_SHORTCUT"
    chmod +x "$DESKTOP_SHORTCUT"
    if command -v gio >/dev/null 2>&1; then
        gio set "$DESKTOP_SHORTCUT" metadata::trusted true 2>/dev/null || true
    fi
    echo "✓ Raccourci créé sur votre Bureau : $DESKTOP_SHORTCUT"
fi

echo "✓ Application ajoutée à votre menu des applications Linux !"
echo ""
echo "Lancement immédiat du jeu..."
exec "$BIN" "$@"
