
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock usb package and submodules BEFORE importing pacman_interceptor
mock_usb = MagicMock()
mock_usb_core = MagicMock()
mock_usb_util = MagicMock()

sys.modules["usb"] = mock_usb
sys.modules["usb.core"] = mock_usb_core
sys.modules["usb.util"] = mock_usb_util

# Mock stdout.isatty for Colors class initialization
sys.stdout.isatty = MagicMock(return_value=True)

# Ensure pacman_toolkit is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Now we can import the module under test
import pacman_toolkit.pacman_interceptor as interceptor

class TestCatchMtk(unittest.TestCase):

    def setUp(self):
        # Create a mock device object
        self.mock_dev = MagicMock()
        self.mock_dev.idVendor = 0x0e8d
        self.mock_dev.idProduct = 0x2000 # Example

        # Mock the global spinner to avoid actual output
        interceptor.spinner = MagicMock()
        interceptor.spinner.running = True

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.chmod')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_local_success(self, mock_exists, mock_exit, mock_chmod, mock_call):
        """Test catch_mtk success path when local mtkclient exists."""
        # Setup: Local mtk exists
        # interceptor.MTK_PATH is defined at module level.
        mtk_path = interceptor.MTK_PATH
        local_mtk = os.path.join(mtk_path, "mtk")

        # Mock os.path.exists to return True specifically for the local mtk path check
        def side_effect(path):
            if path == local_mtk:
                return True
            # For other checks (like RESCUE_SCRIPT), we can return True or rely on the actual file system
            # But simpler to just mock it all as True for success path, or check if it matters.
            # The catch_mtk function calls os.path.exists for local mtk.
            return True

        mock_exists.side_effect = side_effect
        mock_call.return_value = 0 # Success for both calls (mtk payload and rescue script)

        # Run
        interceptor.catch_mtk(self.mock_dev)

        # Verify
        # First call: mtk payload using local python script
        expected_cmd = ["python3", local_mtk, "payload"]
        mock_call.assert_any_call(expected_cmd)

        # Second call: rescue script
        rescue_script = interceptor.RESCUE_SCRIPT
        mock_call.assert_any_call([rescue_script, "mtk"])

        # Verify spinner stopped
        interceptor.spinner.stop.assert_called()

        # Verify chmod
        mock_chmod.assert_called_with(rescue_script, 0o755)

        # Verify exit
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.chmod')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_system_success(self, mock_exists, mock_exit, mock_chmod, mock_call):
        """Test catch_mtk success path when local mtkclient is missing (fallback to system)."""
        # Setup: Local mtk DOES NOT exist
        # We need to make sure the check for local mtk returns False
        mtk_path = interceptor.MTK_PATH
        local_mtk = os.path.join(mtk_path, "mtk")

        def side_effect(path):
            if path == local_mtk:
                return False
            return True # Allow other checks to pass if any

        mock_exists.side_effect = side_effect
        mock_call.return_value = 0 # Success

        # Run
        interceptor.catch_mtk(self.mock_dev)

        # Verify
        # First call: mtk payload (system command)
        expected_cmd = ["mtk", "payload"]
        mock_call.assert_any_call(expected_cmd)

        # Verify exit
        mock_exit.assert_called_with(0)

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.chmod')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_payload_fail(self, mock_exists, mock_exit, mock_chmod, mock_call):
        """Test catch_mtk handling when payload command fails."""
        # Setup: Payload fails
        mock_call.return_value = 1
        mock_exists.return_value = False # Default to system mtk, doesn't matter for failure check

        # Run
        interceptor.catch_mtk(self.mock_dev)

        # Verify
        mock_call.assert_called_once() # Only one call (payload)

        # Should NOT exit or run rescue script
        mock_exit.assert_not_called()
        mock_chmod.assert_not_called()

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.sys.exit')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_exception(self, mock_exists, mock_exit, mock_call):
        """Test catch_mtk exception handling."""
        # Setup: Exception raised during subprocess call
        mock_call.side_effect = Exception("Test Exception")
        mock_exists.return_value = False

        # Run
        # Should not crash, just log and return
        try:
            interceptor.catch_mtk(self.mock_dev)
        except Exception:
            self.fail("catch_mtk raised Exception unexpectedly!")

        # Verify
        mock_exit.assert_not_called()

if __name__ == '__main__':
    unittest.main()
