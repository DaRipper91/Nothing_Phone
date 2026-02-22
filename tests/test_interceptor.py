
import sys
import os
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

# Set USBError to Exception globally and immediately
mock_usb_core.USBError = Exception

# Mock stdout.isatty for Colors class initialization
sys.stdout.isatty = MagicMock(return_value=True)

# Add pacman_toolkit to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    import pacman_toolkit.pacman_interceptor as interceptor
except ImportError as e:
    print(f"ImportError: {e}")
    sys.exit(1)

class TestCatchFastboot(unittest.TestCase):
    def setUp(self):
        # Reset mocks
        mock_usb.reset_mock()
        mock_usb_core.reset_mock()
        mock_usb_util.reset_mock()

        # Ensure USBError is preserved/reset correctly
        mock_usb_core.USBError = Exception

        # Mock constants
        mock_usb_util.ENDPOINT_OUT = 0
        mock_usb_util.ENDPOINT_IN = 0x80

        # Mock sys.stdout.isatty for Colors
        self.patcher_isatty = patch('sys.stdout.isatty', return_value=True)
        self.mock_isatty = self.patcher_isatty.start()

        # Mock os.chmod
        self.patcher_chmod = patch('os.chmod')
        self.mock_chmod = self.patcher_chmod.start()

        # Mock sys.exit
        self.patcher_exit = patch('sys.exit')
        self.mock_exit = self.patcher_exit.start()

        # Mock subprocess
        self.patcher_subprocess = patch('pacman_toolkit.pacman_interceptor.subprocess')
        self.mock_subprocess = self.patcher_subprocess.start()

        # Create a mock device
        self.mock_dev = MagicMock()
        self.mock_dev.idVendor = 0x18d1
        self.mock_dev.idProduct = 0x4ee0

        # Reset globals if needed
        interceptor.spinner = MagicMock()

    def tearDown(self):
        self.patcher_isatty.stop()
        self.patcher_chmod.stop()
        self.patcher_exit.stop()
        self.patcher_subprocess.stop()

    @patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.find_descriptor')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.dispose_resources')
    def test_catch_fastboot_success(self, mock_dispose, mock_find, mock_claim):
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
        self.mock_chmod.assert_called()
        self.mock_subprocess.call.assert_called()
        self.mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.find_descriptor')
    def test_catch_fastboot_detach_error(self, mock_find, mock_claim):
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
        self.mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface')
    @patch('pacman_toolkit.pacman_interceptor.usb.util.find_descriptor')
    def test_catch_fastboot_read_timeout(self, mock_find, mock_claim):
        # Setup: descriptors found
        mock_ep_out = MagicMock()
        mock_ep_in = MagicMock()
        mock_find.side_effect = [mock_ep_out, mock_ep_in]

        # Simulate USBError on read
        mock_ep_in.read.side_effect = interceptor.usb.core.USBError("Timeout")

        # Execute
        interceptor.catch_fastboot(self.mock_dev)

        # Verify read attempted
        mock_ep_in.read.assert_called()

        # Verify flow continued to script execution
        self.mock_subprocess.call.assert_called()
        self.mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.log')
    def test_catch_fastboot_exception(self, mock_log):
        # Setup: claim_interface raises generic Exception
        with patch('pacman_toolkit.pacman_interceptor.usb.util.claim_interface', side_effect=Exception("Generic Error")):
            interceptor.catch_fastboot(self.mock_dev)

            # Verify error logged
            mock_log.assert_called_with("Fastboot Catch Error: Generic Error", interceptor.Colors.FAIL)

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

if __name__ == '__main__':
    unittest.main()
