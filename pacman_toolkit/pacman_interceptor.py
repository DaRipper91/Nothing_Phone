#!/usr/bin/env python3
import usb.core
import usb.util
import subprocess
import time
import sys
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Configuration
TOOLKIT_DIR = os.path.dirname(os.path.realpath(__file__))
# Check for mtkclient in toolkit dir, otherwise assume system path or relative
MTK_PATH = os.path.join(TOOLKIT_DIR, "mtkclient")
RESCUE_SCRIPT = os.path.join(TOOLKIT_DIR, "flash_rescue.sh")

# Identifiers
VID_GOOGLE = 0x18d1
VID_NOTHING = 0x2b4c
VID_MEDIATEK = 0x0e8d
TARGET_VIDS = {VID_GOOGLE, VID_NOTHING, VID_MEDIATEK}

# Known Fastboot Product IDs
KNOWN_FASTBOOT_PIDS = {0x4ee0, 0xd001}  # Common Fastboot PIDs
NOTHING_FASTBOOT_PIDS = {0x4ee0, 0xd001}  # Nothing Phone Fastboot PIDs

# Retry configuration
MAX_RETRIES = 10
INITIAL_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 30.0  # seconds
POLLING_INTERVAL = 0.1  # seconds (10Hz) - reduced from 200Hz to save CPU

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

class Spinner:
    def __init__(self, message="Waiting"):
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.idx = 0
        self.message = message
        self.last_update = 0
        self.update_interval = 0.1
        self.running = False

    def start(self):
        if not self.running:
            self.running = True
            sys.stdout.write(f"\r{self.spinner_chars[self.idx]} {self.message}")
            sys.stdout.flush()
            self.last_update = time.time()

    def update(self):
        if not self.running:
            return
        current_time = time.time()
        if current_time - self.last_update > self.update_interval:
            self.idx = (self.idx + 1) % len(self.spinner_chars)
            sys.stdout.write(f"\r{self.spinner_chars[self.idx]} {self.message}")
            sys.stdout.flush()
            self.last_update = current_time

    def stop(self):
        if self.running:
            sys.stdout.write("\r" + " " * (len(self.message) + 2) + "\r")
            sys.stdout.flush()
            self.running = False

# Global spinner instance
spinner = None

def log(msg, color=None):
    global spinner
    was_running = False
    if spinner and spinner.running:
        spinner.stop()
        was_running = True

    if color:
        logger.info(f"{color}[PACMAN-INTERCEPTOR] {msg}{Colors.ENDC}")
    else:
        logger.info(f"[PACMAN-INTERCEPTOR] {msg}")

    if was_running:
        spinner.start()

def catch_fastboot(dev):
    log(f"Fastboot Device Detected: {hex(dev.idVendor)}:{hex(dev.idProduct)}", Colors.GREEN)
    try:
        # Detach kernel driver to ensure we can claim it
        if dev.is_kernel_driver_active(0):
            try:
                dev.detach_kernel_driver(0)
            except usb.core.USBError:
                pass

        # Claim interface
        usb.util.claim_interface(dev, 0)

        # Find endpoints
        cfg = dev.get_active_configuration()
        intf = cfg[(0,0)]

        ep_out = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)
        ep_in = usb.util.find_descriptor(intf, custom_match=lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

        if ep_out and ep_in:
            # Send 'getvar:all' to freeze bootloader
            log("Sending 'getvar:all' to freeze bootloader...")
            ep_out.write(b'getvar:all')

            # Attempt to read response to confirm command receipt
            try:
                ep_in.read(64, timeout=100)
            except usb.core.USBError as e:
                logger.debug(f"USB read timeout or error (expected): {e}")
                pass

        # Release resources so flash_rescue.sh (fastboot tool) can take over
        usb.util.dispose_resources(dev)

        log("Device frozen. Invoking Flash Rescue (Fastboot Mode)...", Colors.GREEN)
        if spinner:
            spinner.stop()

        # Ensure executable
        os.chmod(RESCUE_SCRIPT, 0o755)
        subprocess.call([RESCUE_SCRIPT, "fastboot"])
        sys.exit(0)

    except Exception as e:
        log(f"Fastboot Catch Error: {e}", Colors.FAIL)

def catch_mtk(dev):
    log(f"MediaTek Device Detected: {hex(dev.idVendor)}:{hex(dev.idProduct)}", Colors.GREEN)
    log("Attempting to trigger mtkclient payload...", Colors.CYAN)

    # We construct the command to run mtkclient
    # Prefer local mtkclient if present
    if os.path.exists(os.path.join(MTK_PATH, "mtk")):
        cmd = ["python3", os.path.join(MTK_PATH, "mtk"), "payload"]
    else:
        # Fallback to assuming it's in PATH or installed as module
        cmd = ["mtk", "payload"]

    try:
        # We use call to wait for it. mtk payload should handle the handshake.
        ret = subprocess.call(cmd)
        if ret == 0:
            log("Payload successful. Invoking Flash Rescue (MTK Mode)...", Colors.GREEN)
            if spinner:
                spinner.stop()
            os.chmod(RESCUE_SCRIPT, 0o755)
            subprocess.call([RESCUE_SCRIPT, "mtk"])
            sys.exit(0)
        else:
            log("mtkclient payload failed.", Colors.FAIL)
    except Exception as e:
        log(f"MTK Launch Error: {e}", Colors.FAIL)

def print_instructions():
    print("\n" + Colors.BOLD + "="*50 + Colors.ENDC)
    print(f"      {Colors.HEADER}Nothing Phone 2(a) Recovery Toolkit{Colors.ENDC}")
    print(Colors.BOLD + "="*50 + Colors.ENDC)
    print(f"1. Force shutdown: Hold {Colors.CYAN}Vol+{Colors.ENDC} and {Colors.CYAN}Power{Colors.ENDC} until screen is black")
    print(f"2. Enter recovery: Immediately hold {Colors.CYAN}Vol+{Colors.ENDC}, {Colors.CYAN}Vol-{Colors.ENDC} and {Colors.CYAN}Power{Colors.ENDC}")
    print(f"3. {Colors.GREEN}Connect USB cable{Colors.ENDC} while holding all three buttons")
    print(Colors.BOLD + "="*50 + Colors.ENDC + "\n")
    print("\n" + Colors.HEADER + "="*50)
    print("      Nothing Phone 2(a) Recovery Toolkit")
    print("="*50 + Colors.ENDC)
    print(f"1. Force shutdown: Hold {Colors.CYAN}Vol+{Colors.ENDC} and {Colors.CYAN}Power{Colors.ENDC} until screen is black")
    print(f"2. Enter recovery: Immediately hold {Colors.CYAN}Vol+{Colors.ENDC}, {Colors.CYAN}Vol-{Colors.ENDC} and {Colors.CYAN}Power{Colors.ENDC}")
    print("3. Connect USB cable while holding all three buttons")
    print(Colors.HEADER + "="*50 + Colors.ENDC + "\n")

def check_prerequisites():
    if not os.path.exists(RESCUE_SCRIPT):
        logger.error(f"Rescue script not found: {RESCUE_SCRIPT}")
        sys.exit(1)

    firmware_dir = os.path.join(TOOLKIT_DIR, "firmware")
    if not os.path.isdir(firmware_dir):
        logger.error(f"{Colors.FAIL}Firmware directory not found: {firmware_dir}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}Please create the firmware directory and place your images there:{Colors.ENDC}")
        print(f"  {Colors.GREEN}mkdir -p {firmware_dir}{Colors.ENDC}")
        sys.exit(1)

    # Check for minimal files (boot.img is critical for both modes)
    if not os.path.exists(os.path.join(firmware_dir, "boot.img")):
        logger.error(f"{Colors.FAIL}boot.img not found in firmware directory!{Colors.ENDC}")
        print(f"{Colors.WARNING}Please place official firmware images in pacman_toolkit/firmware/{Colors.ENDC}")
        sys.exit(1)

def handle_catch_error(dev_addr, exception, device_type, failed_devices, retry_counts):
    """Handles and tracks failures during device catch attempts."""
    failed_devices[dev_addr] = (
        failed_devices.get(dev_addr, (0, 0))[0] + 1,
        time.time()
    )
    retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
    logger.warning(f"Failed to catch {device_type} device (attempt {retry_counts[dev_addr]}): {exception}")

def main():
    global spinner

    check_prerequisites()
    print_instructions()

    log("Starting Pacman Interceptor...", Colors.BOLD)
    log("  Target VIDs: 0x18d1 (Google), 0x2b4c (Nothing), 0x0e8d (MediaTek)")
    
    spinner = Spinner(f"{Colors.CYAN}🔎 Waiting for device connection... (Press Ctrl+C to stop){Colors.ENDC}")
    spinner = Spinner(f"{Colors.BLUE}🔎 Waiting for device connection... (Press Ctrl+C to stop){Colors.ENDC}")
    spinner.start()

    # Track failed catch attempts to implement cooldown
    failed_devices = {}  # Maps device address to (failure_count, last_attempt_time)
    retry_counts = {}  # Maps device address to retry count

    while True:
        try:
            if spinner:
                spinner.update()

            # find_all=True is faster than creating new context repeatedly?
            # Actually usb.core.find returns an iterator.
            devs = usb.core.find(find_all=True)

            for dev in devs:
                # Optimization: Skip irrelevant devices early to save CPU
                if dev.idVendor not in TARGET_VIDS:
                    continue

                # Create unique device identifier
                dev_addr = (dev.idVendor, dev.idProduct, dev.bus, dev.address)
                
                # Check if we should apply cooldown for this device
                if dev_addr in failed_devices:
                    next_retry_time, failure_count = failed_devices[dev_addr]
                    
                    if time.time() < next_retry_time:
                        # Still in cooldown period, skip this device
                        continue
                    
                    # Check if we've exceeded max retries
                    if dev_addr in retry_counts and retry_counts[dev_addr] >= MAX_RETRIES:
                        log(f"Max retries ({MAX_RETRIES}) exceeded for device {dev_addr}", Colors.FAIL)
                        log("Unable to catch device. Possible causes:", Colors.FAIL)
                        log("  - Device bootloop window too short", Colors.FAIL)
                        log("  - USB connection unstable", Colors.FAIL)
                        log("  - Incorrect device permissions", Colors.FAIL)
                        log("Please reconnect the device and try again.", Colors.FAIL)
                        logger.error(f"Max retries ({MAX_RETRIES}) exceeded for device {dev_addr[0]:04x}:{dev_addr[1]:04x}:{dev_addr[2]}:{dev_addr[3]}")
                        logger.error("Unable to catch device. Possible causes:")
                        logger.error("  - Device bootloop window too short")
                        logger.error("  - USB connection unstable")
                        logger.error("  - Incorrect device permissions")
                        logger.error("Please reconnect the device and try again.")
                        sys.exit(1)
                
                # Filter by VID and PID
                if dev.idVendor == VID_GOOGLE:
                    # Only catch if it's a known Fastboot PID
                    if dev.idProduct in KNOWN_FASTBOOT_PIDS:
                        try:
                            catch_fastboot(dev)
                        except Exception as e:
                            # Track failure
                            current_count = failed_devices.get(dev_addr, (0, 0))[1]
                            new_count = current_count + 1
                            backoff = min(INITIAL_BACKOFF * (2 ** new_count), MAX_BACKOFF)
                            failed_devices[dev_addr] = (
                                time.time() + backoff,
                                new_count
                            )
                            retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
                            log(f"Failed to catch fastboot device (attempt {retry_counts[dev_addr]}): {e}", Colors.WARNING)
                            handle_catch_error(dev_addr, e, "fastboot", failed_devices, retry_counts)
                elif dev.idVendor == VID_NOTHING:
                    # Only catch if it's a known Nothing Fastboot PID
                    if dev.idProduct in NOTHING_FASTBOOT_PIDS:
                        try:
                            catch_fastboot(dev)
                        except Exception as e:
                            # Track failure
                            current_count = failed_devices.get(dev_addr, (0, 0))[1]
                            new_count = current_count + 1
                            backoff = min(INITIAL_BACKOFF * (2 ** new_count), MAX_BACKOFF)
                            failed_devices[dev_addr] = (
                                time.time() + backoff,
                                new_count
                            )
                            retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
                            log(f"Failed to catch fastboot device (attempt {retry_counts[dev_addr]}): {e}", Colors.WARNING)
                            handle_catch_error(dev_addr, e, "fastboot", failed_devices, retry_counts)
                elif dev.idVendor == VID_MEDIATEK:
                    try:
                        catch_mtk(dev)
                    except Exception as e:
                        # Track failure
                        current_count = failed_devices.get(dev_addr, (0, 0))[1]
                        new_count = current_count + 1
                        backoff = min(INITIAL_BACKOFF * (2 ** new_count), MAX_BACKOFF)
                        failed_devices[dev_addr] = (
                            time.time() + backoff,
                            new_count
                        )
                        retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
                        log(f"Failed to catch MTK device (attempt {retry_counts[dev_addr]}): {e}", Colors.WARNING)
                        handle_catch_error(dev_addr, e, "MTK", failed_devices, retry_counts)

            # Minimal sleep to prevent CPU hogging, but keep it tight
            # Increased to 50ms to reduce idle CPU usage while maintaining responsiveness
            time.sleep(0.05)
            time.sleep(POLLING_INTERVAL)

        except usb.core.USBError as e:
            logger.debug(f"USB enumeration error (transient): {e}")
            continue
        except KeyboardInterrupt:
            if spinner:
                spinner.stop()
            log("Aborted.")
            break
        except Exception:
            if spinner:
                spinner.stop()
            raise

if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Ensure cursor is cleared on crash
        if spinner:
            spinner.stop()
        raise
