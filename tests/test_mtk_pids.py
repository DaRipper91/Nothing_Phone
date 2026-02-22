import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import importlib

# Ensure pacman_toolkit is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestMtkPids(unittest.TestCase):
    def setUp(self):
        # Create mocks for usb
        mock_usb = MagicMock()
        mock_usb_core = MagicMock()
        mock_usb_util = MagicMock()
        # Ensure USBError exists
        class MockUSBError(Exception):
            pass
        mock_usb_core.USBError = MockUSBError
        mock_usb.core = mock_usb_core

        # Patch sys.modules
        with patch.dict(sys.modules, {
            'usb': mock_usb,
            'usb.core': mock_usb_core,
            'usb.util': mock_usb_util
        }):
            import pacman_toolkit.pacman_interceptor
            importlib.reload(pacman_toolkit.pacman_interceptor)
            self.interceptor = pacman_toolkit.pacman_interceptor

        # Reset spinner
        self.interceptor.spinner = None

        # Mocks for usb.core to be used in test
        self.mock_usb_core = mock_usb_core

    @patch('time.sleep')
    @patch('pacman_toolkit.pacman_interceptor.catch_mtk')
    def test_mtk_pid_check(self, mock_catch_mtk, mock_sleep):
        """Verify that catch_mtk is only called for valid MTK PIDs."""

        # Create mock devices
        # Device 1: Valid MTK BROM
        dev_brom = MagicMock()
        dev_brom.idVendor = 0x0e8d
        dev_brom.idProduct = 0x0003
        dev_brom.bus = 1
        dev_brom.address = 1

        # Device 2: Valid MTK Preloader
        dev_preloader = MagicMock()
        dev_preloader.idVendor = 0x0e8d
        dev_preloader.idProduct = 0x2000
        dev_preloader.bus = 1
        dev_preloader.address = 2

        # Device 3: Invalid MTK Device
        dev_invalid = MagicMock()
        dev_invalid.idVendor = 0x0e8d
        dev_invalid.idProduct = 0x1234  # Random PID
        dev_invalid.bus = 1
        dev_invalid.address = 3

        # Set up find return value on the Mock usb.core that interceptor uses
        # Since interceptor.usb.core IS mock_usb_core (because we patched sys.modules during reload)
        # BUT sys.modules['usb.core'] was restored after reload.
        # So interceptor.usb.core holds the Mock object created in setUp.

        # We need to set return_value on THAT object.
        self.mock_usb_core.find.return_value = [dev_brom, dev_preloader, dev_invalid]

        # Force main loop to exit after one iteration
        class LoopExit(Exception):
            pass

        mock_sleep.side_effect = LoopExit("Exiting main loop")

        # Also need to patch check_prerequisites to avoid filesystem checks
        with patch.object(self.interceptor, 'check_prerequisites'), \
             patch.object(self.interceptor, 'print_instructions'):

            # Run main() and catch the exit exception
            try:
                self.interceptor.main()
            except LoopExit:
                pass
            except Exception as e:
                self.fail(f"Unexpected exception: {e}")

        # Verify calls
        # We verify mock_catch_mtk was called.
        # mock_catch_mtk is passed via decorator.
        # This patches interceptor.catch_mtk (on the reloaded module).

        calls = mock_catch_mtk.call_args_list
        called_devices = [c[0][0] for c in calls]

        # Assertions
        self.assertIn(dev_brom, called_devices, "Valid BROM PID should be caught")
        self.assertIn(dev_preloader, called_devices, "Valid Preloader PID should be caught")
        self.assertNotIn(dev_invalid, called_devices, "Invalid PID should NOT be caught")

        self.assertEqual(mock_catch_mtk.call_count, 2)

if __name__ == '__main__':
    unittest.main()
