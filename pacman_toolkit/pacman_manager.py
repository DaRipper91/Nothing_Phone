#!/usr/bin/env python3
import os
import sys
import time
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Constants
TOOLKIT_DIR = os.path.dirname(os.path.realpath(__file__))
FIRMWARE_DIR = os.path.join(TOOLKIT_DIR, "firmware")
PACMAN_INTERCEPTOR = os.path.join(TOOLKIT_DIR, "pacman_interceptor.py")

class Colors:
    _is_tty = sys.stdout.isatty()
    HEADER = '\033[95m' if _is_tty else ''
    BLUE = '\033[94m' if _is_tty else ''
    CYAN = '\033[96m' if _is_tty else ''
    GREEN = '\033[92m' if _is_tty else ''
    WARNING = '\033[93m' if _is_tty else ''
    FAIL = '\033[91m' if _is_tty else ''
    ENDC = '\033[0m' if _is_tty else ''
    BOLD = '\033[1m' if _is_tty else ''
    UNDERLINE = '\033[4m' if _is_tty else ''

def print_header():
    os.system('cls' if os.name == 'nt' else 'clear')
    print(Colors.HEADER + "="*60 + Colors.ENDC)
    print(f"{Colors.BOLD}      Nothing Phone 2(a) Manager Toolkit (Pacman){Colors.ENDC}")
    print(Colors.HEADER + "="*60 + Colors.ENDC)
    print("")

def find_file_interactive(filename, description="firmware file"):
    """
    Finds a file interactively.
    1. Checks common paths.
    2. Asks user to search hidden paths.
    3. Asks user for manual path.
    """
    print(f"{Colors.CYAN}Searching for {description} ('{filename}')...{Colors.ENDC}")

    # 1. Common Paths
    common_paths = [
        FIRMWARE_DIR,
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Documents"),
        os.path.expanduser("~/Desktop"),
        os.getcwd()
    ]

    for path in common_paths:
        candidate = os.path.join(path, filename)
        if os.path.exists(candidate):
            print(f"{Colors.GREEN}Found at: {candidate}{Colors.ENDC}")
            return candidate

    print(f"{Colors.WARNING}File '{filename}' not found in common locations.{Colors.ENDC}")

    # 2. Hidden / Uncommon Paths
    choice = input(f"Do you want to search in hidden/uncommon folders (this might take a while)? (y/n): ").strip().lower()
    if choice == 'y':
        print(f"{Colors.CYAN}Searching user home directory...{Colors.ENDC}")
        home = os.path.expanduser("~")
        # Walk through home directory
        for root, dirs, files in os.walk(home):
            # Optimizations: Skip heavy directories
            if '.git' in dirs: dirs.remove('.git')
            if 'node_modules' in dirs: dirs.remove('node_modules')
            if '.cache' in dirs: dirs.remove('.cache') # Optional, but often huge

            if filename in files:
                candidate = os.path.join(root, filename)
                print(f"{Colors.GREEN}Found at: {candidate}{Colors.ENDC}")
                return candidate
        print(f"{Colors.WARNING}File not found in hidden search.{Colors.ENDC}")

    # 3. Manual Input
    while True:
        path = input(f"Please enter the full path to '{filename}' (or 'q' to quit/download): ").strip()
        if path.lower() == 'q':
            break

        # Check if user entered a directory or file
        if os.path.isdir(path):
            candidate = os.path.join(path, filename)
            if os.path.exists(candidate):
                return candidate
            else:
                print(f"{Colors.FAIL}File '{filename}' not found in that directory.{Colors.ENDC}")
        elif os.path.isfile(path):
            if os.path.basename(path) == filename:
                return path
            else:
                # Allow different filename if user insists?
                # "You selected 'other_file.img'. Is this correct? (y/n)"
                confirm = input(f"{Colors.WARNING}Filename '{os.path.basename(path)}' does not match '{filename}'. Use anyway? (y/n): {Colors.ENDC}").strip().lower()
                if confirm == 'y':
                    return path
        else:
             print(f"{Colors.FAIL}Path does not exist.{Colors.ENDC}")

    # 4. Download Instructions
    print(f"\n{Colors.WARNING}File not found. Please download it manually.{Colors.ENDC}")
    print(f"Refer to FIRMWARE_GUIDE.md or visit: https://github.com/spike0en/nothing_archive")
    return None

def unlock_bootloader():
    print_header()
    print(f"{Colors.BOLD}=== Unlock Bootloader ==={Colors.ENDC}")
    print(f"{Colors.WARNING}WARNING: Unlocking the bootloader will WIPE ALL DATA on your device!{Colors.ENDC}")
    print(f"{Colors.WARNING}Proceed with caution.{Colors.ENDC}")

    confirm = input("Type 'YES' to continue: ").strip()
    if confirm != 'YES':
        print("Operation cancelled.")
        return

    print(f"\n{Colors.CYAN}Please put your device in Fastboot Mode (Vol- + Power).{Colors.ENDC}")
    input("Press Enter when device is connected in Fastboot mode...")

    try:
        # Check connection
        subprocess.check_call(["fastboot", "devices"])

        print("Unlocking...")
        subprocess.check_call(["fastboot", "flashing", "unlock"])

        print(f"{Colors.GREEN}Unlock command sent. Please confirm on device screen (Vol keys to select, Power to confirm).{Colors.ENDC}")
    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}Error unlocking bootloader: {e}{Colors.ENDC}")
    except FileNotFoundError:
        print(f"{Colors.FAIL}Error: 'fastboot' command not found. Please install android-tools.{Colors.ENDC}")

    input("\nPress Enter to return to menu...")

def flash_root():
    print_header()
    print(f"{Colors.BOLD}=== Root Device (Flash Patched Boot) ==={Colors.ENDC}")

    filename = input("Enter the name of your rooted boot image (default: magisk_patched.img): ").strip()
    if not filename:
        filename = "magisk_patched.img"

    image_path = find_file_interactive(filename, "rooted boot image")

    if not image_path:
        print(f"{Colors.FAIL}Rooting aborted. Image not found.{Colors.ENDC}")
        input("\nPress Enter to return to menu...")
        return

    print(f"\n{Colors.CYAN}Please put your device in Fastboot Mode (Vol- + Power).{Colors.ENDC}")
    input("Press Enter when device is connected in Fastboot mode...")

    try:
        # Check connection
        subprocess.check_call(["fastboot", "devices"])

        print(f"Flashing {filename} to boot_a...")
        subprocess.check_call(["fastboot", "flash", "boot_a", image_path])

        print(f"Flashing {filename} to boot_b...")
        subprocess.check_call(["fastboot", "flash", "boot_b", image_path])

        print(f"{Colors.GREEN}Flashing complete! Rebooting...{Colors.ENDC}")
        subprocess.call(["fastboot", "reboot"])

    except subprocess.CalledProcessError as e:
        print(f"{Colors.FAIL}Error flashing root image: {e}{Colors.ENDC}")
    except FileNotFoundError:
         print(f"{Colors.FAIL}Error: 'fastboot' command not found. Please install android-tools.{Colors.ENDC}")

    input("\nPress Enter to return to menu...")

def run_interceptor():
    # We call the interceptor script using the same python interpreter
    print(f"{Colors.CYAN}Starting Pacman Interceptor...{Colors.ENDC}")
    try:
        subprocess.call([sys.executable, PACMAN_INTERCEPTOR])
    except KeyboardInterrupt:
        pass

def main_menu():
    while True:
        print_header()
        print("1. Rescue / Unbrick (Interceptor Mode)")
        print("2. Unlock Bootloader")
        print("3. Root Device (Flash Rooted Image)")
        print("4. Exit")

        choice = input("\nSelect an option (1-4): ").strip()

        if choice == '1':
            run_interceptor()
        elif choice == '2':
            unlock_bootloader()
        elif choice == '3':
            flash_root()
        elif choice == '4':
            print("Exiting...")
            sys.exit(0)
        else:
            print(f"{Colors.FAIL}Invalid option.{Colors.ENDC}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
