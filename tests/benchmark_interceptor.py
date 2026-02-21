import sys
import time
import unittest.mock
import os

# Add pacman_toolkit to path
sys.path.append(os.path.join(os.getcwd(), "pacman_toolkit"))

# Mock usb module structure BEFORE importing pacman_interceptor
mock_usb = unittest.mock.MagicMock()
mock_usb_core = unittest.mock.MagicMock()
mock_usb_util = unittest.mock.MagicMock()

# Setup find to return empty iterator
mock_usb_core.find.return_value = iter([])

module_patches = {
    'usb': mock_usb,
    'usb.core': mock_usb_core,
    'usb.util': mock_usb_util,
}

with unittest.mock.patch.dict(sys.modules, module_patches):
    import pacman_interceptor

def run_benchmark():
    # Mock check_prerequisites
    pacman_interceptor.check_prerequisites = lambda: None

    # Capture sleep calls
    sleep_calls = []

    original_sleep = time.sleep

    def mock_sleep(duration):
        sleep_calls.append(duration)
        if len(sleep_calls) >= 10:  # Run for limited calls
            raise StopIteration("Benchmark complete")

    # Patch time.sleep in the module
    pacman_interceptor.time.sleep = mock_sleep

    # Patch usb.core.find in the module (it might have been imported)
    # Since pacman_interceptor does `import usb.core`, we need to patch the attribute on the module
    pacman_interceptor.usb.core.find.return_value = []

    print("Starting benchmark loop...")
    try:
        pacman_interceptor.main()
    except StopIteration:
        pass
    except Exception as e:
        print(f"Benchmark error: {e}")
        # Print stack trace
        import traceback
        traceback.print_exc()

    print(f"Number of sleep calls: {len(sleep_calls)}")
    print(f"Sleep durations: {sleep_calls}")

    total_sleep_per_loop = 0
    if len(sleep_calls) >= 2:
        # Check pattern
        if sleep_calls[0] == 0.05 and sleep_calls[1] == 0.1:
             print("CONFIRMED: Loop has double sleep (0.05s + 0.1s)")
        elif sleep_calls[0] == 0.1 and sleep_calls[1] == 0.05:
             print("CONFIRMED: Loop has double sleep (0.1s + 0.05s)")
        elif sleep_calls[0] == 0.1 and sleep_calls[1] == 0.1:
             print("Loop has single sleep (0.1s)")
        else:
             print(f"Loop sleep pattern: {sleep_calls[:2]}")

if __name__ == "__main__":
    run_benchmark()
