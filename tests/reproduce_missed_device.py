
import time
import unittest.mock
import sys
import os

# Add pacman_toolkit to path
sys.path.append(os.path.join(os.getcwd(), "pacman_toolkit"))

# Mock usb module structure BEFORE importing pacman_interceptor
mock_usb = unittest.mock.MagicMock()
mock_usb_core = unittest.mock.MagicMock()
mock_usb_util = unittest.mock.MagicMock()

# Setup find logic
device_present_window = [0.0, 0.0] # [start_time, end_time]

def mock_find(find_all=True):
    current_time = time.time()
    if device_present_window[0] <= current_time <= device_present_window[1]:
        # Return a device
        dev = unittest.mock.MagicMock()
        dev.idVendor = 0x18d1 # Google VID
        dev.idProduct = 0x4ee0 # Fastboot PID
        # We need to simulate that we found a device, so this is valid.
        return iter([dev])
    return iter([])

mock_usb_core.find.side_effect = mock_find
# Setup USBError as a real exception type so it can be caught
mock_usb_core.USBError = type('USBError', (Exception,), {})

# Link modules
mock_usb.core = mock_usb_core
mock_usb.util = mock_usb_util

module_patches = {
    'usb': mock_usb,
    'usb.core': mock_usb_core,
    'usb.util': mock_usb_util,
}

with unittest.mock.patch.dict(sys.modules, module_patches):
    import pacman_interceptor

def run_test(polling_interval, window_duration=0.075):
    # Set POLLING_INTERVAL
    pacman_interceptor.POLLING_INTERVAL = polling_interval

    # Mock check_prerequisites
    pacman_interceptor.check_prerequisites = lambda: None

    # Mock catch_fastboot to stop the loop when called (simulating success)
    caught = False

    def mock_catch_fastboot(dev):
        nonlocal caught
        caught = True
        raise SystemExit("Caught Device!")

    pacman_interceptor.catch_fastboot = mock_catch_fastboot

    # Set device present window
    start_time = time.time() + 0.02 # Small delay before device appears
    device_present_window[0] = start_time
    device_present_window[1] = start_time + window_duration

    print(f"Testing Interval: {polling_interval}s, Window: {window_duration}s")

    # Run main for a short duration
    start_run = time.time()
    try:
        # Patch time.sleep to use real sleep but stop after duration
        original_sleep = time.sleep
        def controlled_sleep(duration):
            if time.time() - start_run > 0.5: # Run for max 0.5s
                raise StopIteration("Timeout")
            original_sleep(duration)

        pacman_interceptor.time.sleep = controlled_sleep

        # Suppress spinner output
        pacman_interceptor.spinner = None

        pacman_interceptor.main()
    except SystemExit as e:
        if str(e) == "Caught Device!":
            print("RESULT: SUCCESS - Device Caught!")
            return True
        else:
            print(f"RESULT: SystemExit {e}")
            return False
    except StopIteration as e:
        if str(e) == "Timeout":
            print("RESULT: FAILURE - Missed Device (Timeout)")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        # Restore sleep
        pacman_interceptor.time.sleep = original_sleep

    return False

if __name__ == "__main__":
    print("Reproduction Test: Can we catch a device appearing for 75ms?\n")

    success_01 = 0
    success_005 = 0
    runs = 5

    print(f"--- Running {runs} tests with 0.1s interval ---")
    for i in range(runs):
        if run_test(0.1, 0.075):
            success_01 += 1
        time.sleep(0.1)

    print(f"\n--- Running {runs} tests with 0.05s interval ---")
    for i in range(runs):
        if run_test(0.05, 0.075):
            success_005 += 1
        time.sleep(0.1)

    print("\nSummary:")
    print(f"0.1s Interval Success Rate: {success_01}/{runs}")
    print(f"0.05s Interval Success Rate: {success_005}/{runs}")
