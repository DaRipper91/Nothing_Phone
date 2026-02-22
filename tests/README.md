# Tests Directory

This directory contains the unit tests for the Nothing Phone (2a) Repair Tool.

## 📁 Directory Structure

**Parent Directory**: `..` (Root of the repository)

## 📄 File Index

### **[__init__.py](__init__.py)**
*   **Purpose**: Makes this directory a Python package.

### **[test_interceptor.py](test_interceptor.py)** (Assuming exists or will be created)
*   **Purpose**: Tests for `pacman_toolkit/pacman_interceptor.py`.
*   **Function**: Verifies USB interception logic and error handling.
*   **Mocks**: `usb.core`, `usb.util`.

### **[test_manager.py](test_manager.py)**
*   **Purpose**: Tests for `pacman_toolkit/pacman_manager.py`.
*   **Function**: Verifies menu logic and file search functions.
*   **Mocks**: `builtins.input`, `os.path.exists`.

## 🧪 Running Tests

To run the test suite, navigate to the root directory and execute:

```bash
python3 -m unittest discover tests
```
or using pytest:
```bash
pytest
```
