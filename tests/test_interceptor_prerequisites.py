
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

# Mock subprocess to avoid actual calls during import/execution
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

class TestCheckPrerequisites(unittest.TestCase):

    def setUp(self):
        # Reload interceptor to ensure clean state and correct __file__ resolution
        import importlib
        importlib.reload(interceptor)

        # Mock dependencies
        self.mock_logger = patch('pacman_toolkit.pacman_interceptor.logger').start()
        self.mock_exit = patch('sys.exit').start()
        self.mock_print = patch('builtins.print').start()

        # Determine paths used in the module
        self.rescue_script = interceptor.RESCUE_SCRIPT
        self.firmware_dir = os.path.join(interceptor.TOOLKIT_DIR, "firmware")
        self.boot_img = os.path.join(self.firmware_dir, "boot.img")

        # Make sys.exit raise SystemExit so execution stops
        self.mock_exit.side_effect = SystemExit

    def tearDown(self):
        patch.stopall()

    @patch('pacman_toolkit.pacman_interceptor.os.path.isdir')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_all_prerequisites_met(self, mock_exists, mock_isdir):
        """Test that check_prerequisites succeeds when all files exist."""
        # Setup mocks to return True
        mock_exists.return_value = True
        mock_isdir.return_value = True

        # Call function
        interceptor.check_prerequisites()

        # Verify
        self.mock_exit.assert_not_called()
        self.mock_logger.error.assert_not_called()

    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_missing_rescue_script(self, mock_exists):
        """Test that check_prerequisites fails when rescue script is missing."""
        # Setup mock to fail on rescue script check
        # interceptor.RESCUE_SCRIPT is checked first
        def side_effect(path):
            if path == self.rescue_script:
                return False
            return True

        mock_exists.side_effect = side_effect

        # Call function and expect exit
        with self.assertRaises(SystemExit):
            interceptor.check_prerequisites()

        # Verify
        self.mock_exit.assert_called_once_with(1)
        # Check if logger was called with appropriate message
        args, _ = self.mock_logger.error.call_args
        self.assertIn("Rescue script not found", args[0])

    @patch('pacman_toolkit.pacman_interceptor.os.path.isdir')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_missing_firmware_dir(self, mock_exists, mock_isdir):
        """Test that check_prerequisites fails when firmware directory is missing."""
        # Setup mocks
        mock_exists.return_value = True # Rescue script exists
        mock_isdir.return_value = False # Firmware dir does not exist

        # Call function and expect exit
        with self.assertRaises(SystemExit):
            interceptor.check_prerequisites()

        # Verify
        self.mock_exit.assert_called_once_with(1)
        # Check if logger was called with appropriate message
        args, _ = self.mock_logger.error.call_args
        self.assertIn("Firmware directory not found", args[0])

    @patch('pacman_toolkit.pacman_interceptor.os.path.isdir')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_missing_boot_img(self, mock_exists, mock_isdir):
        """Test that check_prerequisites fails when boot.img is missing."""
        # Setup mocks
        mock_isdir.return_value = True # Firmware dir exists

        def side_effect(path):
            if path == self.rescue_script:
                return True
            if path == self.boot_img:
                return False
            return True

        mock_exists.side_effect = side_effect

        # Call function and expect exit
        with self.assertRaises(SystemExit):
            interceptor.check_prerequisites()

        # Verify
        self.mock_exit.assert_called_once_with(1)
        # Check if logger was called with appropriate message
        args, _ = self.mock_logger.error.call_args
        self.assertIn("boot.img not found", args[0])

if __name__ == '__main__':
    unittest.main()
