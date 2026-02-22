#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Constants
TOOLKIT_DIR = os.path.join(os.getcwd(), "pacman_toolkit")
FIRMWARE_DIR = os.path.join(TOOLKIT_DIR, "firmware")

REQUIRED_FILES = {
    'boot.img': 'Kernel Image',
    'vbmeta.img': 'Verified Boot Metadata'
}

OPTIONAL_MTK_FILES = {
    'preloader.img': 'MTK Preloader (Must be named exactly preloader.img)',
    'lk.img': 'Little Kernel (Bootloader)'
}

# Also accept raw names to rename them
RAW_NAMES = {
    'preloader_raw.img': 'preloader.img',
    'lk': 'lk.img',
    'lk.bin': 'lk.img'
}

def print_header():
    print(Colors.HEADER + "="*60 + Colors.ENDC)
    print(f"{Colors.BOLD}   Nothing Phone (2a) Repair Tool - Setup & Verification{Colors.ENDC}")
    print(Colors.HEADER + "="*60 + Colors.ENDC)
    print("")

def check_system():
    print(f"\n{Colors.CYAN}[1/3] Checking System Environment...{Colors.ENDC}")

    # Check OS
    if not os.path.exists("/etc/arch-release"):
        print(f"{Colors.WARNING}Warning: This toolkit is optimized for Arch Linux. You may encounter issues on other distributions.{Colors.ENDC}")
    else:
        print(f"{Colors.GREEN}Arch Linux detected.{Colors.ENDC}")

    # Check pacman
    if shutil.which("pacman") is None:
        print(f"{Colors.FAIL}Error: 'pacman' package manager not found. This script requires an Arch-based system for automatic installation.{Colors.ENDC}")
        print("Please install dependencies manually based on your distribution.")
        return False
    return True

def install_packages():
    print(f"\n{Colors.CYAN}[2/3] Checking Dependencies...{Colors.ENDC}")
    packages = [
        "base-devel", "git", "python", "python-pip",
        "libusb", "android-tools", "python-pyusb", "python-libusb1"
    ]

    missing = []
    for pkg in packages:
        # Check if installed
        try:
            if subprocess.call(["pacman", "-Qi", pkg], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) != 0:
                missing.append(pkg)
        except FileNotFoundError:
            print(f"{Colors.WARNING}Skipping dependency check (pacman not found).{Colors.ENDC}")
            return False

    if missing:
        print(f"{Colors.WARNING}Missing packages: {', '.join(missing)}{Colors.ENDC}")
        choice = input(f"Install missing packages? (y/n): ").strip().lower()
        if choice == 'y':
            print("Installing...")
            try:
                subprocess.check_call(["sudo", "pacman", "-S", "--needed", "--noconfirm"] + missing)
                print(f"{Colors.GREEN}Packages installed successfully.{Colors.ENDC}")
            except subprocess.CalledProcessError:
                print(f"{Colors.FAIL}Failed to install packages. Please run: sudo pacman -S {' '.join(missing)}{Colors.ENDC}")
                return False
        else:
            print(f"{Colors.WARNING}Skipping package installation. Some features may not work.{Colors.ENDC}")
    else:
        print(f"{Colors.GREEN}All required system packages are installed.{Colors.ENDC}")

    return True

def find_file(filename, search_paths):
    for path in search_paths:
        candidate = os.path.join(path, filename)
        if os.path.exists(candidate):
            return candidate
    return None

def setup_firmware():
    print(f"\n{Colors.CYAN}[3/3] Setting up Firmware...{Colors.ENDC}")

    # Create firmware directory
    if not os.path.exists(FIRMWARE_DIR):
        print(f"Creating firmware directory: {FIRMWARE_DIR}")
        os.makedirs(FIRMWARE_DIR)

    search_paths = [
        os.getcwd(),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Desktop"),
        FIRMWARE_DIR # Also check if they are already there
    ]

    found_count = 0

    # 1. Look for standard files
    all_targets = list(REQUIRED_FILES.keys()) + list(OPTIONAL_MTK_FILES.keys())

    for target in all_targets:
        if os.path.exists(os.path.join(FIRMWARE_DIR, target)):
            print(f"{Colors.GREEN}Found {target} in firmware directory.{Colors.ENDC}")
            found_count += 1
            continue

        found_path = find_file(target, search_paths)
        if found_path:
            print(f"{Colors.GREEN}Found {target} at {found_path}{Colors.ENDC}")
            shutil.copy2(found_path, os.path.join(FIRMWARE_DIR, target))
            print(f"Copied to {FIRMWARE_DIR}")
            found_count += 1
        else:
            print(f"{Colors.WARNING}Missing: {target}{Colors.ENDC}")

    # 2. Look for files needing rename (e.g. preloader_raw.img)
    for raw_name, new_name in RAW_NAMES.items():
        # Check if destination already exists
        if os.path.exists(os.path.join(FIRMWARE_DIR, new_name)):
            continue

        found_path = find_file(raw_name, search_paths)
        if found_path:
            print(f"{Colors.GREEN}Found {raw_name} (will be renamed to {new_name}){Colors.ENDC}")
            confirm = input(f"Copy and rename '{raw_name}' to '{new_name}'? (y/n): ").strip().lower()
            if confirm == 'y':
                shutil.copy2(found_path, os.path.join(FIRMWARE_DIR, new_name))
                print(f"Copied and renamed to {FIRMWARE_DIR}/{new_name}")
                found_count += 1

    if found_count == 0:
        print(f"\n{Colors.FAIL}No firmware files found.{Colors.ENDC}")
        print(f"Please download firmware from: https://github.com/spike0en/nothing_archive")
        print(f"Place files in: {FIRMWARE_DIR} or ~/Downloads")
    else:
        print(f"\n{Colors.GREEN}Firmware setup complete. {found_count} files ready.{Colors.ENDC}")

def finalize_setup():
    print(f"\n{Colors.CYAN}Finalizing permissions...{Colors.ENDC}")
    scripts = ["pacman_interceptor.py", "flash_rescue.sh"]
    for script in scripts:
        path = os.path.join(TOOLKIT_DIR, script)
        if os.path.exists(path):
            os.chmod(path, 0o755)
            print(f"Made executable: {script}")
        else:
            print(f"{Colors.WARNING}Warning: {script} not found.{Colors.ENDC}")

if __name__ == "__main__":
    print_header()

    # System Check
    if not check_system():
        print(f"{Colors.WARNING}System check failed, but continuing for manual setup...{Colors.ENDC}")

    # Dependencies
    if not install_packages():
        print(f"{Colors.WARNING}Dependency installation skipped or failed.{Colors.ENDC}")

    # Firmware
    setup_firmware()

    # Finalize
    finalize_setup()

    print(f"\n{Colors.BOLD}{Colors.GREEN}Setup Complete!{Colors.ENDC}")
    print(f"To run the repair tool: sudo python3 pacman_toolkit/pacman_interceptor.py")
