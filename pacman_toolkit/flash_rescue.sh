#!/bin/bash

# Enable strict error handling
set -e
set -o pipefail

# Configuration
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
FIRMWARE_DIR="${SCRIPT_DIR}/firmware"
# We expect mtkclient to be a folder in toolkit
MTK_CLIENT="${SCRIPT_DIR}/mtkclient/mtk"

MODE=$1

# Track operations for summary report
declare -a OPERATIONS_SUCCESS=()
declare -a OPERATIONS_FAILED=()

# Function to validate firmware files
validate_firmware_files() {
    local mode=$1
    local all_present=true
    
    echo "[PACMAN-RESCUE] Validating firmware files..."
    
    if [ "$mode" == "fastboot" ]; then
        # Files needed for fastboot mode
        local required_files=(
            "boot.img"
            "vbmeta.img"
        )
        
        for file in "${required_files[@]}"; do
            if [ -f "$FIRMWARE_DIR/$file" ]; then
                echo "  ✅ $file"
            else
                echo "  ❌ $file - MISSING"
                all_present=false
            fi
        done
        
    elif [ "$mode" == "mtk" ]; then
        # Files needed for MTK mode
        local required_files=(
            "preloader.img"
            "lk.img"
            "boot.img"
            "vbmeta.img"
        )
        
        for file in "${required_files[@]}"; do
            if [ -f "$FIRMWARE_DIR/$file" ]; then
                echo "  ✅ $file"
            else
                echo "  ❌ $file - MISSING"
                all_present=false
            fi
        done
    fi
    
    if [ "$all_present" = false ]; then
        echo ""
        echo "Error: One or more required firmware files are missing!"
        echo "Please ensure all firmware files are present in: $FIRMWARE_DIR"
        exit 1
    fi
    
    echo "  All required files present ✓"
    echo ""
}

# Function to execute command with error handling
exec_with_check() {
    local cmd="$1"
    local description="$2"
    
    echo "[PACMAN-RESCUE] $description..."
    
    if eval "$cmd"; then
        OPERATIONS_SUCCESS+=("$description")
        echo "  ✓ Success"
        return 0
    else
        OPERATIONS_FAILED+=("$description")
        echo "  ✗ FAILED"
        print_summary
        echo ""
        echo "Error: $description failed!"
        echo "Flash operation aborted to prevent further damage."
        exit 1
    fi
}

# Function to print summary report
print_summary() {
    echo ""
    echo "=========================================="
    echo "       FLASH OPERATION SUMMARY"
    echo "=========================================="
    
    if [ ${#OPERATIONS_SUCCESS[@]} -gt 0 ]; then
        echo "✅ Successful operations:"
        for op in "${OPERATIONS_SUCCESS[@]}"; do
            echo "   - $op"
        done
    fi
    
    if [ ${#OPERATIONS_FAILED[@]} -gt 0 ]; then
        echo ""
        echo "❌ Failed operations:"
        for op in "${OPERATIONS_FAILED[@]}"; do
            echo "   - $op"
        done
    fi
    
    echo "=========================================="
}

if [ -z "$MODE" ]; then
    echo "Usage: $0 [fastboot|mtk]"
    exit 1
fi

echo "[PACMAN-RESCUE] Starting Rescue in mode: $MODE"

if [ ! -d "$FIRMWARE_DIR" ]; then
    echo "Error: Firmware directory not found at $FIRMWARE_DIR"
    exit 1
fi

# Validate all required firmware files before starting
validate_firmware_files "$MODE"

if [ "$MODE" == "fastboot" ]; then
    if ! command -v fastboot &> /dev/null; then
        echo "Error: fastboot not found in PATH"
        exit 1
    fi

    exec_with_check "fastboot flash boot_a '$FIRMWARE_DIR/boot.img'" "Flash boot_a partition"
    exec_with_check "fastboot flash boot_b '$FIRMWARE_DIR/boot.img'" "Flash boot_b partition"
    exec_with_check "fastboot flash --disable-verity --disable-verification vbmeta_a '$FIRMWARE_DIR/vbmeta.img'" "Flash vbmeta_a partition (disable verity)"
    exec_with_check "fastboot flash --disable-verity --disable-verification vbmeta_b '$FIRMWARE_DIR/vbmeta.img'" "Flash vbmeta_b partition (disable verity)"

    print_summary
    
    echo ""
    echo "[PACMAN-RESCUE] All operations completed successfully!"
    echo "[PACMAN-RESCUE] Rebooting device..."
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

    echo "[PACMAN-RESCUE] Flashing via mtkclient..."

    # Preloader (Critical)
    exec_with_check "$MTK_CMD w preloader '$FIRMWARE_DIR/preloader.img'" "Flash preloader partition"
    exec_with_check "$MTK_CMD w preloader_b '$FIRMWARE_DIR/preloader.img'" "Flash preloader_b partition"

    # LK / Bootloader
    exec_with_check "$MTK_CMD w lk '$FIRMWARE_DIR/lk.img'" "Flash lk partition"
    exec_with_check "$MTK_CMD w lk2 '$FIRMWARE_DIR/lk.img'" "Flash lk2 partition"

    # Boot
    exec_with_check "$MTK_CMD w boot_a '$FIRMWARE_DIR/boot.img'" "Flash boot_a partition"
    exec_with_check "$MTK_CMD w boot_b '$FIRMWARE_DIR/boot.img'" "Flash boot_b partition"

    # VBMeta
    exec_with_check "$MTK_CMD w vbmeta_a '$FIRMWARE_DIR/vbmeta.img' --verified-boot-disable" "Flash vbmeta_a partition (disable verified boot)"
    exec_with_check "$MTK_CMD w vbmeta_b '$FIRMWARE_DIR/vbmeta.img' --verified-boot-disable" "Flash vbmeta_b partition (disable verified boot)"

    print_summary
    
    echo ""
    echo "[PACMAN-RESCUE] All operations completed successfully!"
    echo "[PACMAN-RESCUE] Rescue Complete. Disconnect and hold Vol+ & Power."

else
    echo "Unknown mode: $MODE"
    exit 1
fi
