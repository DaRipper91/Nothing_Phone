
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

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
try:
    from pacman_toolkit import pacman_interceptor as interceptor
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

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

        # Reset globals if needed, though functions are mostly stateless except for logging/spinner
        interceptor.spinner = MagicMock()

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.chmod')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.find_descriptor')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.dispose_resources')
    def test_catch_fastboot_success(self, mock_dispose, mock_find, mock_claim, mock_exit, mock_chmod, mock_call):
        # Setup mock behavior
        self.mock_dev.is_kernel_driver_active.return_value = True

        # Mock endpoints
        mock_ep_out = MagicMock()
        mock_ep_in = MagicMock()

        # find_descriptor is called twice (out, in)
        mock_find.side_effect = [mock_ep_out, mock_ep_in]

        # Execute
        interceptor.catch_fastboot(self.mock_dev)

        # Verify
        self.mock_dev.detach_kernel_driver.assert_called_with(0)
        mock_claim.assert_called_with(self.mock_dev, 0)
        mock_ep_out.write.assert_called_with(b'getvar:all')
        mock_dispose.assert_called_with(self.mock_dev)
        mock_chmod.assert_called()
        mock_call.assert_called()
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.find_descriptor')
    def test_catch_fastboot_detach_error(self, mock_find, mock_claim, mock_exit, mock_call):
        # Setup: detach_kernel_driver raises USBError
        self.mock_dev.is_kernel_driver_active.return_value = True
        self.mock_dev.detach_kernel_driver.side_effect = interceptor.usb.core.USBError('Test Error')

        # Mock endpoints
        mock_ep_out = MagicMock()
        mock_ep_in = MagicMock()
        mock_find.side_effect = [mock_ep_out, mock_ep_in]

        # Execute
        interceptor.catch_fastboot(self.mock_dev)

        # Verify execution proceeded past the error
        mock_claim.assert_called()
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.log')
    def test_catch_fastboot_exception(self, mock_log):
        # Setup: claim_interface raises generic Exception
        with patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface', side_effect=Exception("Generic Error")):
            interceptor.catch_fastboot(self.mock_dev)

            # Verify error logged
            mock_log.assert_called_with("Fastboot Catch Error: Generic Error", interceptor.Colors.FAIL)

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.find_descriptor')
    @patch('pacman_toolkit.pacman_interceptor.log')
    def test_catch_fastboot_missing_endpoints(self, mock_log, mock_find, mock_claim, mock_exit, mock_call):
        """
        Test that if endpoints are missing, the code logs an error and does NOT call the rescue script.
        """
        # Setup: find_descriptor returns None (missing endpoints)
        mock_find.return_value = None

        # Execute
        interceptor.catch_fastboot(self.mock_dev)

        # Verify descriptors were sought but not found (returned None)
        # find_descriptor is called twice
        self.assertEqual(mock_find.call_count, 2)

        # Verify script executed (SHOULD BE ZERO)
        mock_call.assert_not_called()

        # Verify exit called (SHOULD BE ZERO)
        mock_exit.assert_not_called()

        # Verify error logged
        # Expected: log(f"Fastboot Catch Error: {e}", Colors.FAIL)
        # The exception raised is Exception("Required endpoints (IN/OUT) not found")
        error_found = False
        for call in mock_log.call_args_list:
            args, _ = call
            if args and "Fastboot Catch Error" in str(args[0]) and "Required endpoints" in str(args[0]):
                error_found = True
                break

        self.assertTrue(error_found, "Expected error message not found in logs")

class TestCatchMtk(unittest.TestCase):
    def setUp(self):
        self.mock_dev = MagicMock()
        interceptor.spinner = MagicMock()

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.chmod')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_success(self, mock_exists, mock_exit, mock_chmod, mock_call):
        # Setup: payload succeeds (returns 0)
        mock_call.side_effect = [0, 0] # First call for payload, second for rescue script
        mock_exists.return_value = True # Assume mtk exists locally

        # Execute
        interceptor.catch_mtk(self.mock_dev)

        # Verify
        self.assertEqual(mock_call.call_count, 2)
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.log')
    def test_catch_mtk_payload_fail(self, mock_log, mock_call):
        # Setup: payload fails (returns 1)
        mock_call.return_value = 1

        # Execute
        interceptor.catch_mtk(self.mock_dev)

        # Verify
        mock_log.assert_any_call("mtkclient payload failed.", interceptor.Colors.FAIL)

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.log')
    def test_catch_mtk_exception(self, mock_log, mock_call):
        # Setup: subprocess.call raises Exception
        mock_call.side_effect = Exception("Launch Error")

        # Execute
        interceptor.catch_mtk(self.mock_dev)

        # Verify
        mock_log.assert_called_with("MTK Launch Error: Launch Error", interceptor.Colors.FAIL)

class TestCheckPrerequisites(unittest.TestCase):
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    def test_missing_rescue_script(self, mock_exit, mock_exists):
        # Setup: rescue script missing
        mock_exists.return_value = False

        # Execute
        interceptor.check_prerequisites()

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
        interceptor.check_prerequisites()

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
        interceptor.check_prerequisites()

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
        interceptor.check_prerequisites()

        # Verify
        mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
