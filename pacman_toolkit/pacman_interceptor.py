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

# Known Fastboot Product IDs
KNOWN_FASTBOOT_PIDS = {0x4ee0, 0xd001}  # Common Fastboot PIDs
NOTHING_FASTBOOT_PIDS = {0x4ee0, 0xd001}  # Nothing Phone Fastboot PIDs

# Retry configuration
MAX_RETRIES = 10
INITIAL_BACKOFF = 2.0  # seconds
MAX_BACKOFF = 30.0  # seconds

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

def log(msg):
    global spinner
    was_running = False
    if spinner and spinner.running:
        spinner.stop()
        was_running = True

    logger.info(f"[PACMAN-INTERCEPTOR] {msg}")

    if was_running:
        spinner.start()

def catch_fastboot(dev):
    log(f"Fastboot Device Detected: {hex(dev.idVendor)}:{hex(dev.idProduct)}")
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

        log("Device frozen. Invoking Flash Rescue (Fastboot Mode)...")
        if spinner:
            spinner.stop()

        # Ensure executable
        os.chmod(RESCUE_SCRIPT, 0o755)
        subprocess.call([RESCUE_SCRIPT, "fastboot"])
        sys.exit(0)

    except Exception as e:
        log(f"Fastboot Catch Error: {e}")

def catch_mtk(dev):
    log(f"MediaTek Device Detected: {hex(dev.idVendor)}:{hex(dev.idProduct)}")
    log("Attempting to trigger mtkclient payload...")

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
            log("Payload successful. Invoking Flash Rescue (MTK Mode)...")
            if spinner:
                spinner.stop()
            os.chmod(RESCUE_SCRIPT, 0o755)
            subprocess.call([RESCUE_SCRIPT, "mtk"])
            sys.exit(0)
        else:
            log("mtkclient payload failed.")
    except Exception as e:
        log(f"MTK Launch Error: {e}")

def main():
    global spinner
    log("Starting Pacman Interceptor...")
    log("  Target VIDs: 0x18d1 (Google), 0x2b4c (Nothing), 0x0e8d (MediaTek)")
    
    spinner = Spinner("🔎 Waiting for device connection... (Press Ctrl+C to stop)")
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
                # Create unique device identifier
                dev_addr = f"{dev.idVendor:04x}:{dev.idProduct:04x}:{dev.bus}:{dev.address}"
                
                # Check if we should apply cooldown for this device
                if dev_addr in failed_devices:
                    failure_count, last_attempt = failed_devices[dev_addr]
                    current_time = time.time()
                    
                    # Calculate backoff time with exponential backoff
                    backoff_time = min(INITIAL_BACKOFF * (2 ** failure_count), MAX_BACKOFF)
                    
                    if current_time - last_attempt < backoff_time:
                        # Still in cooldown period, skip this device
                        continue
                    
                    # Check if we've exceeded max retries
                    if dev_addr in retry_counts and retry_counts[dev_addr] >= MAX_RETRIES:
                        logger.error(f"Max retries ({MAX_RETRIES}) exceeded for device {dev_addr}")
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
                            failed_devices[dev_addr] = (
                                failed_devices.get(dev_addr, (0, 0))[0] + 1,
                                time.time()
                            )
                            retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
                            logger.warning(f"Failed to catch fastboot device (attempt {retry_counts[dev_addr]}): {e}")
                elif dev.idVendor == VID_NOTHING:
                    # Only catch if it's a known Nothing Fastboot PID
                    if dev.idProduct in NOTHING_FASTBOOT_PIDS:
                        try:
                            catch_fastboot(dev)
                        except Exception as e:
                            # Track failure
                            failed_devices[dev_addr] = (
                                failed_devices.get(dev_addr, (0, 0))[0] + 1,
                                time.time()
                            )
                            retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
                            logger.warning(f"Failed to catch fastboot device (attempt {retry_counts[dev_addr]}): {e}")
                elif dev.idVendor == VID_MEDIATEK:
                    try:
                        catch_mtk(dev)
                    except Exception as e:
                        # Track failure
                        failed_devices[dev_addr] = (
                            failed_devices.get(dev_addr, (0, 0))[0] + 1,
                            time.time()
                        )
                        retry_counts[dev_addr] = retry_counts.get(dev_addr, 0) + 1
                        logger.warning(f"Failed to catch MTK device (attempt {retry_counts[dev_addr]}): {e}")

            # Minimal sleep to prevent CPU hogging, but keep it tight
            time.sleep(0.005)

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
