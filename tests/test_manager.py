import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Add the repo root to sys.path so we can import pacman_toolkit
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pacman_toolkit import pacman_manager

class TestPacmanManager(unittest.TestCase):

    @patch('os.path.exists')
    def test_find_file_interactive_common_path(self, mock_exists):
        # Case 1: File found in common location
        # common_paths in manager includes FIRMWARE_DIR which is absolute.
        # We mock exists to return True if the path looks like what we expect.

        def side_effect(path):
            return path.endswith("boot.img") and "firmware" in path

        mock_exists.side_effect = side_effect

        # We need to capture stdout to avoid cluttering test output
        with patch('builtins.print'):
            result = pacman_manager.find_file_interactive("boot.img")

        self.assertIsNotNone(result)
        self.assertTrue(result.endswith("boot.img"))

    @patch('builtins.input', side_effect=['y'])
    @patch('os.walk')
    @patch('os.path.exists')
    def test_find_file_interactive_hidden(self, mock_exists, mock_walk, mock_input):
        # Case 2: File not found in common, found in hidden
        mock_exists.return_value = False # Not in common paths

        # Mock os.walk to return a hit in a hidden folder
        # root, dirs, files
        mock_walk.return_value = [
            ('/home/user/.hidden', [], ['secret.img'])
        ]

        with patch('builtins.print'):
            result = pacman_manager.find_file_interactive("secret.img")

        self.assertIsNotNone(result)
        self.assertEqual(result, '/home/user/.hidden/secret.img')

    @patch('builtins.input', side_effect=['n', '/custom/path/custom.img'])
    @patch('os.path.isfile')
    @patch('os.path.isdir')
    @patch('os.path.exists')
    def test_find_file_interactive_manual(self, mock_exists, mock_isdir, mock_isfile, mock_input):
        # Case 3: Manual input
        # First loop: common paths check -> returns False
        # Second loop: hidden search prompt -> 'n'
        # Third loop: manual input -> '/custom/path/custom.img'

        # mock_exists is called for common paths. We want it to fail there.
        # It is also called inside the manual input block?
        # In manual block:
        # if os.path.isdir(path): ...
        # elif os.path.isfile(path): ...

        mock_exists.return_value = False
        mock_isdir.return_value = False
        mock_isfile.return_value = True # It is a file

        with patch('builtins.print'):
            result = pacman_manager.find_file_interactive("custom.img")

        self.assertEqual(result, '/custom/path/custom.img')

    @patch('builtins.input', side_effect=['n', 'q'])
    @patch('os.path.exists')
    def test_find_file_interactive_not_found(self, mock_exists, mock_input):
        # Case 4: Not found anywhere, user quits
        mock_exists.return_value = False

        with patch('builtins.print'):
            result = pacman_manager.find_file_interactive("missing.img")

        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()
