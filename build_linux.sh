#!/bin/bash
echo "Building EchecsP2P for Linux..."

# Build executable using spec
echo "Building executable with PyInstaller..."
python3.12 -m PyInstaller --clean -y EchecsP2P.spec

echo "Build complete! Check the 'dist' folder for EchecsP2P."
