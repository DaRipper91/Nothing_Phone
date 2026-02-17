#!/bin/bash

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FIRMWARE_DIR="${SCRIPT_DIR}/firmware"
# We expect mtkclient to be a folder in toolkit
MTK_CLIENT="${SCRIPT_DIR}/mtkclient/mtk"

MODE=$1

if [ -z "$MODE" ]; then
    echo "Usage: $0 [fastboot|mtk]"
    exit 1
fi

echo "[PACMAN-RESCUE] Starting Rescue in mode: $MODE"

if [ ! -d "$FIRMWARE_DIR" ]; then
    echo "Error: Firmware directory not found at $FIRMWARE_DIR"
    exit 1
fi

if [ "$MODE" == "fastboot" ]; then
    if ! command -v fastboot &> /dev/null; then
        echo "Error: fastboot not found in PATH"
        exit 1
    fi

    echo "Flashing Boot partitions..."
    fastboot flash boot_a "$FIRMWARE_DIR/boot.img"
    fastboot flash boot_b "$FIRMWARE_DIR/boot.img"

    echo "Flashing VBMeta partitions (Disable Verity)..."
    fastboot flash --disable-verity --disable-verification vbmeta_a "$FIRMWARE_DIR/vbmeta.img"
    fastboot flash --disable-verity --disable-verification vbmeta_b "$FIRMWARE_DIR/vbmeta.img"

    echo "Rebooting..."
    fastboot reboot

elif [ "$MODE" == "mtk" ]; then
    # Determine mtk command
    if [ -f "$MTK_CLIENT" ] || [ -f "${MTK_CLIENT}.py" ]; then
        MTK_CMD="python3 $MTK_CLIENT"
    else
        if command -v mtk &> /dev/null; then
             MTK_CMD="mtk"
        else
             echo "Error: mtkclient not found. Please install it or place in toolkit dir."
             exit 1
        fi
    fi

    echo "Flashing via mtkclient..."

    # Preloader (Critical)
    $MTK_CMD w preloader "$FIRMWARE_DIR/preloader.img"
    $MTK_CMD w preloader_b "$FIRMWARE_DIR/preloader.img"

    # LK / Bootloader
    $MTK_CMD w lk "$FIRMWARE_DIR/lk.img"
    $MTK_CMD w lk2 "$FIRMWARE_DIR/lk.img"

    # Boot
    $MTK_CMD w boot_a "$FIRMWARE_DIR/boot.img"
    $MTK_CMD w boot_b "$FIRMWARE_DIR/boot.img"

    # VBMeta
    $MTK_CMD w vbmeta_a "$FIRMWARE_DIR/vbmeta.img" --verified-boot-disable
    $MTK_CMD w vbmeta_b "$FIRMWARE_DIR/vbmeta.img" --verified-boot-disable

    echo "Rescue Complete. Disconnect and hold Vol+ & Power."

else
    echo "Unknown mode: $MODE"
    exit 1
fi
