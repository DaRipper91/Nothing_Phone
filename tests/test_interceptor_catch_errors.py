
import sys
import unittest
from unittest.mock import MagicMock, patch

# Mock usb package and submodules BEFORE importing pacman_interceptor
mock_usb = MagicMock()
mock_usb_core = MagicMock()
mock_usb_util = MagicMock()

sys.modules["usb"] = mock_usb
sys.modules["usb.core"] = mock_usb_core
sys.modules["usb.util"] = mock_usb_util

# Ensure accessing usb.util via the usb module returns the same mock
mock_usb.core = mock_usb_core
mock_usb.util = mock_usb_util

# Mock stdout.isatty for Colors class initialization
sys.stdout.isatty = MagicMock(return_value=True)

# Mock subprocess
import subprocess
subprocess.call = MagicMock(return_value=0)

# Import the script to be tested
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import pacman_toolkit.pacman_interceptor as interceptor
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

# Mock check_prerequisites to avoid file checks during import/execution
if hasattr(interceptor, 'check_prerequisites'):
    interceptor.check_prerequisites = MagicMock()

class TestInterceptorCatchErrors(unittest.TestCase):

    def setUp(self):
        # Reset mocks before each test
        mock_usb_util.reset_mock()
        subprocess.call.reset_mock()

        # Mock interceptor.log to capture calls
        self.log_patcher = patch('pacman_toolkit.pacman_interceptor.log')
        self.mock_log = self.log_patcher.start()

        # Mock sys.exit to prevent test exit
        self.exit_patcher = patch('sys.exit')
        self.mock_exit = self.exit_patcher.start()

    def tearDown(self):
        self.log_patcher.stop()
        self.exit_patcher.stop()

    def test_catch_fastboot_claim_interface_error(self):
        """Test that catch_fastboot handles exceptions (e.g. claim_interface failure) correctly."""

        # Setup mock device
        mock_dev = MagicMock()
        mock_dev.idVendor = 0x18d1
        mock_dev.idProduct = 0x4ee0

        # Simulate claim_interface raising an exception
        # Note: In pacman_interceptor.py, it calls usb.util.claim_interface(dev, 0)
        # raising an Exception here simulates a failure during interception
        mock_usb_util.claim_interface.side_effect = Exception("Simulated Fastboot Error")

        # Call the function under test
        interceptor.catch_fastboot(mock_dev)

        # Verification

        # 1. Verify log was called with the error message
        # We expect a call like log(f"Fastboot Catch Error: {e}", Colors.FAIL)
        # Check if any call args contain the expected substring
        error_logged = False
        for call in self.mock_log.call_args_list:
            args, _ = call
            if args and "Fastboot Catch Error" in str(args[0]) and "Simulated Fastboot Error" in str(args[0]):
                error_logged = True
                break

        self.assertTrue(error_logged, "Expected error message not logged")

        # 2. Verify that subprocess.call was NOT called (meaning we didn't proceed to rescue script)
        subprocess.call.assert_not_called()

        # 3. Verify that sys.exit was NOT called (meaning we didn't exit the interceptor loop)
        self.mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
