
import sys
import io
import contextlib
import unittest
from unittest.mock import MagicMock

# Mock usb package and submodules BEFORE importing pacman_interceptor
mock_usb = MagicMock()
mock_usb_core = MagicMock()
mock_usb_util = MagicMock()

sys.modules["usb"] = mock_usb
sys.modules["usb.core"] = mock_usb_core
sys.modules["usb.util"] = mock_usb_util

# Mock subprocess
import subprocess
subprocess.call = MagicMock(return_value=0)

# Import the script to be tested
# Ensure pacman_toolkit is in path
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

class TestInterceptorUX(unittest.TestCase):
    def test_colors_class_attributes(self):
        """Verify that Colors class has the expected ANSI codes."""
        self.assertTrue(hasattr(interceptor, 'Colors'), "Colors class should exist")

        expected_attrs = ['HEADER', 'BLUE', 'CYAN', 'GREEN', 'WARNING', 'FAIL', 'ENDC', 'BOLD', 'UNDERLINE']
        for attr in expected_attrs:
            self.assertTrue(hasattr(interceptor.Colors, attr), f"Colors should have attribute {attr}")
            val = getattr(interceptor.Colors, attr)
            self.assertTrue(val.startswith('\033['), f"Colors.{attr} should be an ANSI escape code")

    def test_log_function_colors(self):
        """Verify that log function correctly wraps messages in color codes."""
        # Capture logging output
        import logging
        logger = logging.getLogger('pacman_toolkit.pacman_interceptor')

        capture_stream = io.StringIO()
        handler = logging.StreamHandler(capture_stream)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            test_msg = "Test Message"
            color_val = interceptor.Colors.GREEN

            # Call log with color
            interceptor.log(test_msg, color=color_val)

            # Flush handler
            handler.flush()
            output = capture_stream.getvalue()

            # Expected format: f"{color}[PACMAN-INTERCEPTOR] {msg}{Colors.ENDC}"
            # Note: The logger formatter adds "[INFO] " prefix usually, but here we capture direct stream handler output
            # which uses the formatter attached to IT.
            # The script uses basicConfig, which sets root logger handler.
            # We added a new handler with default formatter (message only usually).

            # Let's check for the core content
            expected_content = f"{color_val}[PACMAN-INTERCEPTOR] {test_msg}{interceptor.Colors.ENDC}"

            self.assertIn(expected_content, output, "Log output should contain color-wrapped message")

        finally:
            logger.removeHandler(handler)

if __name__ == '__main__':
    unittest.main()
