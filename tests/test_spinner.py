import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import time

# Mock usb module before it's imported by pacman_interceptor
sys.modules['usb'] = MagicMock()
sys.modules['usb.core'] = MagicMock()
sys.modules['usb.util'] = MagicMock()

# Add the parent directory to sys.path to import pacman_toolkit
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pacman_toolkit.pacman_interceptor import Spinner

class TestSpinner(unittest.TestCase):
    def test_init(self):
        # Default initialization
        s = Spinner()
        self.assertEqual(s.message, "Waiting")
        self.assertEqual(s.idx, 0)
        self.assertFalse(s.running)
        self.assertEqual(s.update_interval, 0.1)

        # Custom message initialization
        s2 = Spinner("Loading")
        self.assertEqual(s2.message, "Loading")

    @patch('sys.stdout')
    @patch('time.time')
    def test_start(self, mock_time, mock_stdout):
        mock_time.return_value = 1000.0
        s = Spinner("Testing")
        s.start()

        self.assertTrue(s.running)
        mock_stdout.write.assert_called_with("\r⠋ Testing")
        mock_stdout.flush.assert_called()
        self.assertEqual(s.last_update, 1000.0)

        # Calling start again when already running should do nothing
        mock_stdout.write.reset_mock()
        s.start()
        mock_stdout.write.assert_not_called()

    @patch('sys.stdout')
    @patch('time.time')
    def test_update(self, mock_time, mock_stdout):
        mock_time.return_value = 1000.0
        s = Spinner("Testing")

        # Update when not running should do nothing
        s.update()
        mock_stdout.write.assert_not_called()

        s.start()
        # Reset mock to clear start() calls
        mock_stdout.write.reset_mock()

        # Update before interval should not do anything
        mock_time.return_value = 1000.05
        s.update()
        mock_stdout.write.assert_not_called()

        # Update after interval should change character
        mock_time.return_value = 1000.15
        s.update()
        mock_stdout.write.assert_called_with("\r⠙ Testing")
        self.assertEqual(s.idx, 1)
        self.assertEqual(s.last_update, 1000.15)

        # Subsequent update
        mock_stdout.write.reset_mock()
        mock_time.return_value = 1000.26
        s.update()
        mock_stdout.write.assert_called_with("\r⠹ Testing")
        self.assertEqual(s.idx, 2)
        self.assertEqual(s.last_update, 1000.26)

    @patch('sys.stdout')
    def test_stop(self, mock_stdout):
        s = Spinner("Testing")

        # Stop when not running should do nothing
        s.stop()
        mock_stdout.write.assert_not_called()

        s.start()
        self.assertTrue(s.running)

        mock_stdout.write.reset_mock()
        s.stop()
        self.assertFalse(s.running)
        # It should clear the line: \r + space * (len("Testing") + 2) + \r
        expected_clear = "\r" + " " * (len("Testing") + 2) + "\r"
        mock_stdout.write.assert_called_with(expected_clear)
        mock_stdout.flush.assert_called()
