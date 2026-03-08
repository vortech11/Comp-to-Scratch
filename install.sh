# WARNING THIS BASH FILE WAS CREATED USING CHATGPT
# I DO NOT KNOW HOW TO WRITE BASH
# I DO NOT KNOW IF THIS WILL DO DAMAGE TO YOUR COMPUTER
# ok 🥰

#!/usr/bin/env bash
set -e

REPO="vortech11/Comp-to-Scratch"
BINARY_NAME="scratch"

INSTALL_DIR="/usr/local/bin"
LOCAL_INSTALL="$HOME/.local/bin"

echo "Installing $BINARY_NAME..."

# Detect OS
OS=$(uname -s | tr '[:upper:]' '[:lower:]')

# Detect architecture
ARCH=$(uname -m)
case "$ARCH" in
    x86_64) ARCH="x86_64" ;;
    aarch64|arm64) ARCH="arm64" ;;
    *)
        echo "Unsupported architecture: $ARCH"
        exit 1
        ;;
esac

# Get latest release download URL
DOWNLOAD_URL=$(curl -s https://api.github.com/repos/$REPO/releases/latest \
    | grep "browser_download_url" \
    | grep "$OS-$ARCH" \
    | cut -d '"' -f 4)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "Could not find a release for $OS-$ARCH"
    exit 1
fi

echo "Downloading binary..."
TMP_FILE=$(mktemp)

curl -L "$DOWNLOAD_URL" -o "$TMP_FILE"

# Determine install location
if [ -w "$INSTALL_DIR" ]; then
    DEST="$INSTALL_DIR/$BINARY_NAME"
elif command -v sudo >/dev/null 2>&1; then
    DEST="$INSTALL_DIR/$BINARY_NAME"
    SUDO="sudo"
else
    mkdir -p "$LOCAL_INSTALL"
    DEST="$LOCAL_INSTALL/$BINARY_NAME"
fi

echo "Installing to $DEST"
$SUDO mv "$TMP_FILE" "$DEST"
$SUDO chmod +x "$DEST"

echo "Installation complete!"

if [[ "$DEST" == "$LOCAL_INSTALL/"* ]]; then
    echo ""
    echo "Ensure ~/.local/bin is in your PATH:"
    echo 'export PATH="$HOME/.local/bin:$PATH"'
fi

echo ""
echo "Run:"
echo "  $BINARY_NAME -help"