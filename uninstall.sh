# WARNING THIS BASH FILE WAS CREATED USING CHATGPT
# I DO NOT KNOW HOW TO WRITE BASH
# I DO NOT KNOW IF THIS WILL DO DAMAGE TO YOUR COMPUTER
# ok 🥰

#!/usr/bin/env bash
set -e

BINARY_NAME="scratch"

SYSTEM_PATH="/usr/local/bin/$BINARY_NAME"
LOCAL_PATH="$HOME/.local/bin/$BINARY_NAME"

echo "Uninstalling $BINARY_NAME..."

if [ -f "$SYSTEM_PATH" ]; then
    echo "Removing system install..."
    sudo rm "$SYSTEM_PATH"
    echo "Removed $SYSTEM_PATH"
elif [ -f "$LOCAL_PATH" ]; then
    echo "Removing local install..."
    rm "$LOCAL_PATH"
    echo "Removed $LOCAL_PATH"
else
    echo "$BINARY_NAME not found."
    exit 1
fi

echo "Uninstall complete."