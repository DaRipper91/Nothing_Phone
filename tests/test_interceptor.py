import sys
import unittest
from unittest.mock import MagicMock, patch
import os

# Mock usb and its submodules BEFORE importing pacman_interceptor
mock_usb = MagicMock()
mock_usb_core = MagicMock()
mock_usb_util = MagicMock()

# Configure the mock usb structure
sys.modules["usb"] = mock_usb
sys.modules["usb.core"] = mock_usb_core
sys.modules["usb.util"] = mock_usb_util

# IMPORTANT: Link the submodules to the parent package mock
# This ensures that 'import usb.core' makes 'usb.core' refer to our configured mock
mock_usb.core = mock_usb_core
mock_usb.util = mock_usb_util

# Set USBError to Exception globally and immediately
mock_usb_core.USBError = Exception

# Mock subprocess to prevent side effects
mock_subprocess = MagicMock()
sys.modules["subprocess"] = mock_subprocess

# Mock sys.stdout.isatty to ensure Colors are initialized correctly
# This mimics what test_interceptor_ux.py does to avoid conflicts if this test runs first
sys.stdout.isatty = MagicMock(return_value=True)

# Ensure the toolkit directory is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now import the module under test
from pacman_toolkit import pacman_interceptor

class TestCatchFastboot(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        mock_usb.reset_mock()
        mock_usb_core.reset_mock()
        mock_usb_util.reset_mock()
        mock_subprocess.reset_mock()

        # Ensure USBError is preserved/reset correctly
        mock_usb_core.USBError = Exception

        # Mock constants
        mock_usb_util.ENDPOINT_OUT = 0
        mock_usb_util.ENDPOINT_IN = 0x80

        # Mock sys.stdout.isatty for Colors (redundant but safe)
        self.patcher_isatty = patch('sys.stdout.isatty', return_value=True)
        self.mock_isatty = self.patcher_isatty.start()

        # Mock os.chmod
        self.patcher_chmod = patch('os.chmod')
        self.mock_chmod = self.patcher_chmod.start()

        # Mock sys.exit
        self.patcher_exit = patch('sys.exit')
        self.mock_exit = self.patcher_exit.start()

        # Create a mock device
        self.mock_dev = MagicMock()
        self.mock_dev.idVendor = 0x18d1
        self.mock_dev.idProduct = 0x4ee0

        # Setup find_descriptor to return mock endpoints
        self.mock_ep_out = MagicMock()
        self.mock_ep_in = MagicMock()

        # Configure usb.util.find_descriptor side effect
        # First call is for OUT endpoint, second for IN endpoint
        mock_usb_util.find_descriptor.side_effect = [self.mock_ep_out, self.mock_ep_in]

    def tearDown(self):
        self.patcher_isatty.stop()
        self.patcher_chmod.stop()
        self.patcher_exit.stop()
        # Reset side_effect
        mock_usb_util.find_descriptor.side_effect = None

    def test_catch_fastboot_success(self):
        """Test successful fastboot catch flow."""
        # Setup kernel driver active
        self.mock_dev.is_kernel_driver_active.return_value = True

        # Call the function
        pacman_interceptor.catch_fastboot(self.mock_dev)

        # Verify kernel driver detached
        self.mock_dev.is_kernel_driver_active.assert_called_with(0)
        self.mock_dev.detach_kernel_driver.assert_called_with(0)

        # Verify interface claimed
        mock_usb_util.claim_interface.assert_called_with(self.mock_dev, 0)

        # Verify descriptors found
        self.assertEqual(mock_usb_util.find_descriptor.call_count, 2)

        # Verify command sent
        self.mock_ep_out.write.assert_called_with(b'getvar:all')

        # Verify response read
        self.mock_ep_in.read.assert_called_with(64, timeout=100)

        # Verify resources disposed
        mock_usb_util.dispose_resources.assert_called_with(self.mock_dev)

        # Verify script executed
        self.mock_chmod.assert_called()
        mock_subprocess.call.assert_called()
        args, _ = mock_subprocess.call.call_args
        self.assertIn("flash_rescue.sh", args[0][0])
        self.assertEqual(args[0][1], "fastboot")

        # Verify exit
        self.mock_exit.assert_called_with(0)

    def test_catch_fastboot_detach_error(self):
        """Test resilience to kernel driver detach failure."""
        self.mock_dev.is_kernel_driver_active.return_value = True
        # Simulate USBError on detach
        # We need to make sure the exception raised is an instance of the class we set on the mock
        self.mock_dev.detach_kernel_driver.side_effect = mock_usb_core.USBError("Detach failed")

        # Call function
        pacman_interceptor.catch_fastboot(self.mock_dev)

        # Verify detach was attempted
        self.mock_dev.detach_kernel_driver.assert_called_with(0)

        # Verify flow continued to claim interface
        mock_usb_util.claim_interface.assert_called_with(self.mock_dev, 0)

        # Verify exit called eventually
        self.mock_exit.assert_called_with(0)

    def test_catch_fastboot_read_timeout(self):
        """Test resilience to read timeout."""
        self.mock_dev.is_kernel_driver_active.return_value = False

        # Simulate USBError on read
        self.mock_ep_in.read.side_effect = mock_usb_core.USBError("Timeout")

        # Call function
        pacman_interceptor.catch_fastboot(self.mock_dev)

        # Verify read attempted
        self.mock_ep_in.read.assert_called()

        # Verify flow continued to script execution
        mock_subprocess.call.assert_called()
        self.mock_exit.assert_called_with(0)

    def test_catch_fastboot_general_exception(self):
        """Test handling of unexpected exceptions."""
        # Force an exception early in the process
        self.mock_dev.is_kernel_driver_active.side_effect = Exception("Unexpected error")

        # Call function
        pacman_interceptor.catch_fastboot(self.mock_dev)

        # Verify exit NOT called (function should return after logging error)
        self.mock_exit.assert_not_called()
        # Verify subprocess NOT called
        mock_subprocess.call.assert_not_called()

if __name__ == '__main__':
    unittest.main()
