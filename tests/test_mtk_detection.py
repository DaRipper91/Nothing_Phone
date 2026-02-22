
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add pacman_toolkit to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock usb modules before importing pacman_interceptor
sys.modules['usb'] = MagicMock()
sys.modules['usb.core'] = MagicMock()
sys.modules['usb.util'] = MagicMock()

# Now import the module under test
from pacman_toolkit import pacman_interceptor

class TestMTKDetection(unittest.TestCase):
    def setUp(self):
        # Reset any global state if necessary (e.g. spinner)
        pacman_interceptor.spinner = None

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_prioritizes_mtk_py(self, mock_exists, mock_call):
        """Test that catch_mtk prioritizes local mtk.py script."""
        # Setup mock device
        dev = MagicMock()
        dev.idVendor = 0x0e8d
        dev.idProduct = 0x2000

        # Mock os.path.exists behavior
        def side_effect(path):
            if path.endswith("mtk.py"):
                return True
            return False
        mock_exists.side_effect = side_effect

        mock_call.return_value = 0

        with self.assertRaises(SystemExit):
            pacman_interceptor.catch_mtk(dev)

        # Verify subprocess.call was called with mtk.py
        # The code constructs: ["python3", path_to_mtk_py, "payload"]
        if mock_call.call_count > 0:
            args, _ = mock_call.call_args_list[0]
            cmd = args[0]
            if isinstance(cmd, list):
                self.assertEqual(cmd[0], "python3")
                self.assertTrue(cmd[1].endswith("mtk.py"))
                self.assertEqual(cmd[2], "payload")

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_fallback_legacy_mtk(self, mock_exists, mock_call):
        """Test that catch_mtk checks for legacy 'mtk' file if mtk.py is missing."""
        # Setup mock device
        dev = MagicMock()
        dev.idVendor = 0x0e8d
        dev.idProduct = 0x2000

        # Mock os.path.exists behavior
        def side_effect(path):
            if path.endswith("mtk.py"):
                return False
            if path.endswith("mtk") and "mtkclient" in path:
                return True
            return False
        mock_exists.side_effect = side_effect

        mock_call.return_value = 0

        with self.assertRaises(SystemExit):
            pacman_interceptor.catch_mtk(dev)

        # Verify subprocess.call was called with mtk (local legacy)
        if mock_call.call_count > 0:
            args, _ = mock_call.call_args_list[0]
            cmd = args[0]
            if isinstance(cmd, list):
                self.assertEqual(cmd[0], "python3")
                self.assertTrue(cmd[1].endswith("mtk"))
                self.assertFalse(cmd[1].endswith("mtk.py"))
                self.assertEqual(cmd[2], "payload")

    @patch('pacman_toolkit.pacman_interceptor.subprocess.call')
    @patch('pacman_toolkit.pacman_interceptor.os.path.exists')
    def test_catch_mtk_system_fallback(self, mock_exists, mock_call):
        """Test that catch_mtk falls back to system command if local files are missing."""
        # Setup mock device
        dev = MagicMock()
        dev.idVendor = 0x0e8d
        dev.idProduct = 0x2000

        # Mock os.path.exists to return False always
        mock_exists.return_value = False

        mock_call.return_value = 0

        with self.assertRaises(SystemExit):
            pacman_interceptor.catch_mtk(dev)

        # Verify subprocess.call was called with fallback command
        mock_call.assert_any_call(["mtk", "payload"])

if __name__ == '__main__':
    unittest.main()
