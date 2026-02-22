# Nothing Phone (2a) Repair Tool - Master Manual

Welcome to the comprehensive documentation for the **Nothing Phone (2a) Repair Tool** (formerly Pacman Unbrick Toolkit). This manual consolidates all technical protocols, firmware acquisition guides, and step-by-step usage instructions into a single reference.

## Table of Contents

1.  [Chapter 1: Introduction](#chapter-1-introduction)
2.  [Chapter 2: Technical Protocol](#chapter-2-technical-protocol)
3.  [Chapter 3: Firmware Acquisition](#chapter-3-firmware-acquisition)
4.  [Chapter 4: Installation & Usage](#chapter-4-installation--usage)
5.  [Chapter 5: Troubleshooting](#chapter-5-troubleshooting)

---

## Chapter 1: Introduction

This toolkit provides automated USB interception scripts to unbrick and recover the Nothing Phone 2(a) (codename: Pacman) on Arch Linux systems. It is designed to catch the device during its critical bootloop window and execute emergency flashing procedures.

### Key Features
*   **Fast USB Interception**: Monitors USB bus with sub-500ms response time.
*   **Dual Mode Support**: Works with both Fastboot and MTK BootROM modes.
*   **Automatic Recovery**: Detects device state and flashes appropriate partitions.
*   **Safety Features**: Validates firmware and uses exponential backoff logic.

### Device Information
*   **Device**: Nothing Phone 2(a)
*   **Codename**: Pacman
*   **SoC**: MediaTek Dimensity 7200 Pro (MT6886)
*   **Model**: A142
*   **Supported Host OS**: Arch Linux (optimized for low-latency USB operations)

---

## Chapter 2: Technical Protocol

This section details the underlying mechanisms of the unbrick process, as originally documented in `PROTOCOL.md`.

### 2.1 Arch Linux Environmental Prep
To achieve sub-500ms latency, we utilize a minimal Arch Linux environment with direct kernel access.

**Dependencies**:
We use `android-udev` for base rules and `python-pyusb` for the interceptor.
```bash
sudo pacman -Syu
sudo pacman -S base-devel git python python-pip libusb android-tools python-pyusb python-libusb1
```

**Udev Rules (The "Interceptor" Setup)**:
We bypass `ModemManager` latency and grant immediate permissions.
```bash
sudo cp pacman_toolkit/99-pacman-unbrick.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### 2.2 The Interceptor Script
The `pacman_interceptor.py` script polls the USB bus directly to catch the device within the 500ms bootloop window.

*   **Fastboot Detection**: If the device enters Fastboot (VID 0x18d1/0x2b4c), it immediately sends a raw USB command (`getvar:all`) to freeze the bootloader before it reboots, then launches the rescue flasher.
*   **MTK Detection**: If the device enters BROM/Preloader (VID 0x0e8d), it triggers the `mtkclient` payload mechanism to bypass SLA and stabilize the device in Download Mode.

---

## Chapter 3: Firmware Acquisition

This chapter covers how to obtain the correct firmware files, as originally documented in `FIRMWARE_GUIDE.md`.

### 3.1 Identify Your Firmware Version
Ideally, match the firmware version currently installed on your device or use the latest available version for your region (Global, Europe, India).

### 3.2 Download Source
We use the [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive) as the source for official firmware images.

1.  Open the [Nothing Archive Repository](https://github.com/spike0en/nothing_archive).
2.  Locate **Phone (2a) - Pacman**.
3.  Download the **OTA Images** (click "Here" in the last column).
4.  Download:
    *   `Pacman_...-image-boot.7z`
    *   `Pacman_...-image-firmware.7z`

### 3.3 Extract and Organize
Extract the archives and move the files to `pacman_toolkit/firmware/`.

**For Fastboot Mode:**
*   `boot.img`
*   `vbmeta.img`

**For MTK Mode (Deep Unbrick):**
*   `boot.img`
*   `vbmeta.img`
*   `preloader_raw.img` (Must be renamed to `preloader.img`)
*   `lk.img` (or `lk`)

**⚠️ IMPORTANT:** The toolkit expects specific filenames. Ensure you rename `preloader_raw.img` to `preloader.img`.

---

## Chapter 4: Installation & Usage

This chapter provides the linear steps to run the recovery process, as originally documented in `STEP_BY_STEP_GUIDE.md`.

### 4.1 Preparation
1.  **Check Environment**: Ensure you are running Arch Linux.
2.  **Install Packages**: Use the setup script or manually install dependencies.
3.  **Setup Udev Rules**: Copy `99-pacman-unbrick.rules` to `/etc/udev/rules.d/`.

### 4.2 Run the Interceptor
```bash
cd pacman_toolkit
chmod +x pacman_interceptor.py flash_rescue.sh
sudo ./pacman_interceptor.py
```
Output should indicate: `Waiting for Nothing Phone 2(a) (Pacman)...`

### 4.3 Connect Your Device
Follow this exact sequence:
1.  **Force Shutdown**: Hold **Vol+** and **Power** until the screen goes black.
2.  **Enter Mode**: Immediately switch to holding **Vol+** and **Vol-** and **Power** (all three buttons).
3.  **Connect**: Plug in the USB cable while holding the keys.
4.  **Watch Terminal**:
    *   If **Fastboot** is caught: Script will say "Device frozen" and flash automatically.
    *   If **MTK** is caught: Script will say "Triggering mtkclient". Keep holding buttons until you see "Payload successful".

### 4.4 Post-Rescue
1.  Disconnect USB.
2.  Hold **Vol+** and **Power** to boot into Fastboot Mode.
3.  If the device enters Fastboot, you have successfully unbricked.

---

## Chapter 5: Troubleshooting

*   **"Resource Busy" in Fastboot**: Run `killall adb` and `killall fastboot`. Ensure no other tools are accessing the device.
*   **mtkclient fails**: Ensure you have the latest `mtkclient`. Try running `python mtkclient/mtk payload` manually before connecting.
*   **Device not appearing**: Check `dmesg -w`. Try a USB 2.0 port.
*   **Max Retries Exceeded**: The bootloop window is very short. Keep trying the button combination timing.
