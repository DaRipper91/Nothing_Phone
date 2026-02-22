# Pacman Toolkit Directory

This directory contains the core scripts and configuration files for the Nothing Phone (2a) Repair Tool.

## 📁 Directory Structure

**Parent Directory**: `..` (Root of the repository)

**Child Directories**:
*   `firmware/`: Directory for storing firmware images (`boot.img`, `vbmeta.img`, `preloader.img`, `lk.img`).

## 📄 File Index

### **[pacman_interceptor.py](pacman_interceptor.py)**
*   **Purpose**: The main interceptor script.
*   **Function**: Polls the USB bus for the device in Fastboot or MTK modes during bootloop.
*   **Calls**:
    *   `flash_rescue.sh` (when Fastboot is detected).
    *   `mtkclient` (when MTK is detected, via subprocess).
*   **Dependencies**: `usb.core`, `usb.util` (PyUSB).

### **[flash_rescue.sh](flash_rescue.sh)**
*   **Purpose**: Automated flashing script.
*   **Function**: Executed by `pacman_interceptor.py` to flash partitions once the device is frozen.
*   **Calls**: `fastboot` commands.
*   **Dependencies**: `android-tools`.

### **[pacman_manager.py](pacman_manager.py)**
*   **Purpose**: Interactive CLI/TUI manager.
*   **Function**: Provides a menu for common tasks like launching the interceptor, unlocking bootloader, and rooting.
*   **Calls**: `pacman_interceptor.py`, `fastboot`.

### **[99-pacman-unbrick.rules](99-pacman-unbrick.rules)**
*   **Purpose**: Udev rules file.
*   **Function**: Grants permissions for the device and bypasses ModemManager interference.
*   **Installation**: Copied to `/etc/udev/rules.d/` during setup.

### **[__init__.py](__init__.py)**
*   **Purpose**: Python package initialization.
*   **Function**: Makes this directory a Python package.
