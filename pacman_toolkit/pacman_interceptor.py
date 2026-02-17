#!/usr/bin/env python3
import usb.core
import usb.util
import subprocess
import time
import sys
import os

# Configuration
TOOLKIT_DIR = os.path.dirname(os.path.realpath(__file__))
# Check for mtkclient in toolkit dir, otherwise assume system path or relative
MTK_PATH = os.path.join(TOOLKIT_DIR, "mtkclient")
RESCUE_SCRIPT = os.path.join(TOOLKIT_DIR, "flash_rescue.sh")

# Identifiers
VID_GOOGLE = 0x18d1
VID_NOTHING = 0x2b4c
VID_MEDIATEK = 0x0e8d

def log(msg):
    print(f"[PACMAN-INTERCEPTOR] {msg}")

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
            except:
                pass

        # Release resources so flash_rescue.sh (fastboot tool) can take over
        usb.util.dispose_resources(dev)

        log("Device frozen. Invoking Flash Rescue (Fastboot Mode)...")
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
            os.chmod(RESCUE_SCRIPT, 0o755)
            subprocess.call([RESCUE_SCRIPT, "mtk"])
            sys.exit(0)
        else:
            log("mtkclient payload failed.")
    except Exception as e:
        log(f"MTK Launch Error: {e}")

def main():
    log("Waiting for Nothing Phone 2(a) (Pacman)...")
    log("  Target VIDs: 0x18d1 (Google), 0x2b4c (Nothing), 0x0e8d (MediaTek)")

    while True:
        try:
            # find_all=True is faster than creating new context repeatedly?
            # Actually usb.core.find returns an iterator.
            devs = usb.core.find(find_all=True)

            for dev in devs:
                if dev.idVendor == VID_GOOGLE or dev.idVendor == VID_NOTHING:
                    catch_fastboot(dev)
                elif dev.idVendor == VID_MEDIATEK:
                    catch_mtk(dev)

            # Minimal sleep to prevent CPU hogging, but keep it tight
            time.sleep(0.005)

        except usb.core.USBError:
            continue
        except KeyboardInterrupt:
            log("Aborted.")
            break

if __name__ == "__main__":
    main()
