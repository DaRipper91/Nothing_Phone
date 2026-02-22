# Nothing Phone (2a) Repair Tool

> **⚠️ Formerly known as Pacman Unbrick Toolkit**

A comprehensive, automated repair tool for unbricking and recovering the Nothing Phone 2(a) (codename: Pacman) on Arch Linux systems.

## 📚 Documentation

The complete manual for this toolkit is available in **[Documentation/MASTER_MANUAL.md](Documentation/MASTER_MANUAL.md)**.

The manual includes:
*   **Chapter 1: Introduction** - Overview and features.
*   **Chapter 2: Technical Protocol** - How the interception works.
*   **Chapter 3: Firmware Acquisition** - Where to get files.
*   **Chapter 4: Installation & Usage** - Step-by-step guide.
*   **Chapter 5: Troubleshooting** - Common issues and fixes.

## 🚀 Quick Start

1.  **Run the Setup Script**:
    ```bash
    python3 setup_and_verify.py
    ```
    This script will check dependencies, help you find firmware, and prepare the toolkit.

2.  **Run the Interceptor**:
    ```bash
    sudo python3 pacman_toolkit/pacman_interceptor.py
    ```

For detailed instructions, please consult the [Master Manual](Documentation/MASTER_MANUAL.md).

## 📂 Project Structure

*   **`pacman_toolkit/`**: Core scripts and udev rules.
*   **`Documentation/`**: Master Manual and legacy guides.
*   **`tests/`**: Unit tests for the toolkit.
*   **`setup_and_verify.py`**: Automated setup script.

## ⚠️ Disclaimer

This tool is for educational and recovery purposes. Use at your own risk. Always backup your data if possible.
