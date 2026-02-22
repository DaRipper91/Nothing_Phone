import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import importlib

# We need to ensure we can import pacman_toolkit
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMTKDetection(unittest.TestCase):
    def setUp(self):
        # Prepare environment for import/reload
        # We need to mock usb, but ensure subprocess is REAL so patch works

        # Create mocks for usb
        mock_usb = MagicMock()
        mock_usb_core = MagicMock()
        mock_usb_util = MagicMock()
        # Ensure USBError exists
        mock_usb_core.USBError = Exception
        mock_usb.core = mock_usb_core

        # Patch sys.modules to inject our usb mocks, but KEEP real subprocess
        # We use a context manager for the reload
        with patch.dict(sys.modules, {
            'usb': mock_usb,
            'usb.core': mock_usb_core,
            'usb.util': mock_usb_util
        }):
            import pacman_toolkit.pacman_interceptor
            importlib.reload(pacman_toolkit.pacman_interceptor)
            self.interceptor = pacman_toolkit.pacman_interceptor

        # Reset any global state
        self.interceptor.spinner = MagicMock()

    def test_catch_mtk_prioritizes_mtk_py(self):
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

        with patch.object(self.interceptor.os.path, 'exists', side_effect=side_effect) as mock_exists, \
             patch.object(self.interceptor.subprocess, 'call', return_value=0) as mock_call:

            with self.assertRaises(SystemExit):
                self.interceptor.catch_mtk(dev)

            # Verify subprocess.call was called with mtk.py
            args, _ = mock_call.call_args_list[0]
            cmd = args[0]
            self.assertEqual(cmd[0], "python3")
            self.assertTrue(cmd[1].endswith("mtk.py"))
            self.assertEqual(cmd[2], "payload")

    def test_catch_mtk_fallback_legacy_mtk(self):
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

        with patch.object(self.interceptor.os.path, 'exists', side_effect=side_effect) as mock_exists, \
             patch.object(self.interceptor.subprocess, 'call', return_value=0) as mock_call:

            with self.assertRaises(SystemExit):
                self.interceptor.catch_mtk(dev)

            # Verify subprocess.call was called with mtk (local legacy)
            args, _ = mock_call.call_args_list[0]
            cmd = args[0]
            self.assertEqual(cmd[0], "python3")
            self.assertTrue(cmd[1].endswith("mtk"))
            self.assertFalse(cmd[1].endswith("mtk.py"))
            self.assertEqual(cmd[2], "payload")

    def test_catch_mtk_system_fallback(self):
        """Test that catch_mtk falls back to system command if local files are missing."""
        # Setup mock device
        dev = MagicMock()
        dev.idVendor = 0x0e8d
        dev.idProduct = 0x2000

        with patch.object(self.interceptor.os.path, 'exists', return_value=False) as mock_exists, \
             patch.object(self.interceptor.subprocess, 'call', return_value=0) as mock_call:

            with self.assertRaises(SystemExit):
                self.interceptor.catch_mtk(dev)

            # Verify subprocess.call was called with fallback command
            mock_call.assert_any_call(["mtk", "payload"])

if __name__ == '__main__':
    unittest.main()
