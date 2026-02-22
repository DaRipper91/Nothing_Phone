import unittest
import os
import re

class TestUdevRules(unittest.TestCase):
    def test_udev_rules_permissions(self):
        """
        Ensures that udev rules do not grant overly permissive access (MODE="0666").
        They should use MODE="0660" and GROUP="uucp" to restrict access to the group.
        """
        # Locate the rules file relative to this test file
        rules_path = os.path.join(os.path.dirname(__file__), '..', 'pacman_toolkit', '99-pacman-unbrick.rules')
        self.assertTrue(os.path.exists(rules_path), f"Udev rules file not found at {rules_path}")

        with open(rules_path, 'r') as f:
            content = f.read()

        lines = content.splitlines()
        for i, line in enumerate(lines):
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue

            # Check for rules
            if 'SUBSYSTEM=="usb"' in line:
                # Security Check 1: No world-writable permissions
                self.assertNotIn('MODE="0666"', line,
                    f"Line {i+1}: Found insecure MODE='0666'. Use MODE='0660' instead.")

                # Security Check 2: Correct group assignment
                self.assertIn('GROUP="uucp"', line,
                    f"Line {i+1}: Missing GROUP='uucp' restriction.")

                # Security Check 3: Correct mode assignment
                self.assertIn('MODE="0660"', line,
                    f"Line {i+1}: Missing secure MODE='0660'.")

if __name__ == '__main__':
    unittest.main()
