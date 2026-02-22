import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Create mocks
mock_usb = MagicMock()
mock_usb_core = MagicMock()
mock_usb_util = MagicMock()

# Define a real Exception class for USBError
class MockUSBError(Exception):
    pass
mock_usb_core.USBError = MockUSBError
mock_usb.core = mock_usb_core
mock_usb.util = mock_usb_util

# We will apply patches in setUp to ensure isolation
class TestInterceptor(unittest.TestCase):
    def setUp(self):
        # Patch sys.modules to return our mocks for usb
        self.modules_patcher = patch.dict(sys.modules, {
            'usb': mock_usb,
            'usb.core': mock_usb_core,
            'usb.util': mock_usb_util,
            'subprocess': MagicMock() # Mock subprocess to prevent accidental execution
        })
        self.modules_patcher.start()

        # Add toolkit path
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

        # Import module - we might need to reload if it was already imported
        try:
            import pacman_toolkit.pacman_interceptor as interceptor
            import importlib
            importlib.reload(interceptor)
            self.interceptor = interceptor
        except ImportError as e:
            self.fail(f"Failed to import pacman_interceptor: {e}")

        # Setup common mocks on the imported module
        self.interceptor.spinner = MagicMock()

        # Mock sys.stdout.isatty for Colors
        self.isatty_patcher = patch('sys.stdout.isatty', return_value=True)
        self.isatty_patcher.start()

        # Create a mock device
        self.mock_dev = MagicMock()
        self.mock_dev.idVendor = 0x18d1
        self.mock_dev.idProduct = 0x4ee0

        # Reset global mocks
        mock_usb.reset_mock()
        mock_usb_core.reset_mock()
        mock_usb_util.reset_mock()

        # Mocks for tests
        self.mock_subprocess = sys.modules['subprocess']

    def tearDown(self):
        self.modules_patcher.stop()
        self.isatty_patcher.stop()

class TestCatchFastboot(TestInterceptor):
    @patch('pacman_toolkit.pacman_interceptor.os.chmod')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_catch_fastboot_success(self, mock_exit, mock_chmod):
        """Test successful fastboot catch flow."""
        # Setup kernel driver active
        self.mock_dev.is_kernel_driver_active.return_value = True

        # Mock endpoints
        mock_ep_out = MagicMock()
        mock_ep_in = MagicMock()

        # We need to patch usb.util in the interceptor module
        # Since we reloaded interceptor, interceptor.usb.util is our mock_usb_util
        mock_usb_util.find_descriptor.side_effect = [mock_ep_out, mock_ep_in]

        # Mock subprocess call
        self.mock_subprocess.call.return_value = 0

        # Call the function
        self.interceptor.catch_fastboot(self.mock_dev)

        # Verify kernel driver detached
        self.mock_dev.detach_kernel_driver.assert_called_with(0)

        # Verify interface claimed
        mock_usb_util.claim_interface.assert_called_with(self.mock_dev, 0)

        # Verify descriptors found
        self.assertEqual(mock_usb_util.find_descriptor.call_count, 2)

        # Verify command sent
        mock_ep_out.write.assert_called_with(b'getvar:all')

        # Verify response read
        mock_ep_in.read.assert_called_with(64, timeout=100)

        # Verify resources disposed
        mock_usb_util.dispose_resources.assert_called_with(self.mock_dev)

        # Verify script executed
        mock_chmod.assert_called()
        self.mock_subprocess.call.assert_called()

        # Verify exit
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_catch_fastboot_detach_error(self, mock_exit):
        """Test resilience to kernel driver detach failure."""
        self.mock_dev.is_kernel_driver_active.return_value = True
        # Simulate USBError on detach
        self.mock_dev.detach_kernel_driver.side_effect = MockUSBError("Detach failed")

        # Mock endpoints
        mock_ep_out = MagicMock()
        mock_ep_in = MagicMock()
        mock_usb_util.find_descriptor.side_effect = [mock_ep_out, mock_ep_in]

        # Call function
        self.interceptor.catch_fastboot(self.mock_dev)

        # Verify flow continued to claim interface
        mock_usb_util.claim_interface.assert_called_with(self.mock_dev, 0)

        # Verify exit called eventually
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_catch_fastboot_read_timeout(self, mock_exit):
        """Test resilience to read timeout."""
        self.mock_dev.is_kernel_driver_active.return_value = False

        # Mock endpoints
        mock_ep_out = MagicMock()
        mock_ep_in = MagicMock()
        mock_usb_util.find_descriptor.side_effect = [mock_ep_out, mock_ep_in]

        # Simulate USBError on read
        mock_ep_in.read.side_effect = MockUSBError("Timeout")

        # Call function
        self.interceptor.catch_fastboot(self.mock_dev)

        # Verify flow continued to script execution
        self.mock_subprocess.call.assert_called()
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.log')
    def test_catch_fastboot_general_exception(self, mock_log):
        """Test handling of unexpected exceptions."""
        # Force an exception early in the process
        self.mock_dev.is_kernel_driver_active.side_effect = Exception("Unexpected error")

        # Call function
        self.interceptor.catch_fastboot(self.mock_dev)

        # Verify error logged
        mock_log.assert_called_with("Fastboot Catch Error: Unexpected error", self.interceptor.Colors.FAIL)

class TestCheckPrerequisites(TestInterceptor):
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_missing_rescue_script(self, mock_exit, mock_exists):
        # Setup: rescue script missing
        mock_exists.return_value = False

        # Execute
        self.interceptor.check_prerequisites()

        # Verify
        mock_exit.assert_called_with(1)

    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    @patch('pacman_toolkit.pacman_interceptor.os.path.isdir')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_missing_firmware_dir(self, mock_exit, mock_isdir, mock_exists):
        # Setup: rescue script exists, but firmware dir missing
        mock_exists.return_value = True
        mock_isdir.return_value = False

        # Execute
        self.interceptor.check_prerequisites()

        # Verify
        mock_exit.assert_called_with(1)

    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    @patch('pacman_toolkit.pacman_interceptor.os.path.isdir')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_missing_boot_img(self, mock_exit, mock_isdir, mock_exists):
        # Setup: rescue script exists, firmware dir exists, but boot.img missing
        # exists calls: [rescue_script, boot.img]
        mock_exists.side_effect = [True, False]
        mock_isdir.return_value = True

        # Execute
        self.interceptor.check_prerequisites()

        # Verify
        mock_exit.assert_called_with(1)

    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    @patch('pacman_toolkit.pacman_interceptor.os.path.isdir')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_prerequisites_ok(self, mock_exit, mock_isdir, mock_exists):
        # Setup: all exist
        mock_exists.return_value = True
        mock_isdir.return_value = True

        # Execute
        self.interceptor.check_prerequisites()

        # Verify
        mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
