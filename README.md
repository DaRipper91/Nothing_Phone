# Nothing Phone 2(a) Pacman Unbrick Toolkit

A comprehensive toolkit for unbricking and recovering the Nothing Phone 2(a) (codename: Pacman) on Arch Linux systems. This toolkit provides automated USB interception scripts that catch the device during its bootloop window and execute emergency flashing procedures.

## 🎯 Overview

This toolkit is designed to unbrick Nothing Phone 2(a) devices that are stuck in bootloop or bricked states. It works by:

1. **Intercepting** the device during the critical 500ms bootloop window via USB
2. **Freezing** the bootloader in either Fastboot or MTK mode
3. **Automatically flashing** critical partitions to restore functionality

The toolkit supports two recovery modes:
- **Fastboot Mode**: For devices that can enter standard Fastboot
- **MTK BROM Mode**: For deeply bricked devices requiring MediaTek bootloader access

## 📱 Device Information

- **Device**: Nothing Phone 2(a)
- **Codename**: Pacman
- **SoC**: MediaTek Dimensity 7200 Pro (MT6886)
- **Model**: A142
- **Supported Host OS**: Arch Linux (optimized for low-latency USB operations)

## ✨ Features

- **Fast USB Interception**: Custom Python script monitors USB bus with sub-500ms response time
- **Dual Mode Support**: Works with both Fastboot and MTK BootROM modes
- **Automatic Recovery**: Detects device state and executes appropriate flash procedure
- **Enhanced Logging & Diagnostics**: Centralized error tracking with detailed, human-readable device identifiers for precise troubleshooting.
- **Optimized Performance**: Efficient USB polling (10Hz) and lazy string formatting minimize CPU usage while maintaining responsiveness.
- **Robust Device Identification**: Explicit filtering for Google, Nothing, and MediaTek vendor IDs prevents false positives.
- **Safety Features**: 
  - Pre-flight firmware validation
  - Exponential backoff retry logic
  - Max retry protection
- **ModemManager Bypass**: Custom udev rules prevent interference from system services
- **A/B Partition Support**: Properly flashes both slots for dual-boot devices

## 📋 Prerequisites

### System Requirements
- Arch Linux (for optimal USB latency)
- Root/sudo access for USB operations and udev rule installation
- Working USB 2.0 or 3.0 port (USB 2.0 recommended for better compatibility)

### Required Packages
```bash
sudo pacman -Syu
sudo pacman -S base-devel git python python-pip libusb android-tools python-pyusb python-libusb1
```

### Required Firmware Files
You need the official Nothing OS firmware for your device region. Place these files in `pacman_toolkit/firmware/`:

**For Fastboot Mode:**
- `boot.img` - Kernel image
- `vbmeta.img` - Verified Boot Metadata

**For MTK Mode (complete unbrick):**
- `preloader.img` - Critical bootloader (essential for unbrick)
- `lk.img` - Little Kernel bootloader
- `boot.img` - Kernel image
- `vbmeta.img` - Verified Boot Metadata

**Firmware Source**: [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive)

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/DaRipper91/Nothing-Phone-2-a-.git
cd Nothing-Phone-2-a-
```

### 2. Install Udev Rules
The udev rules provide immediate USB permissions and bypass ModemManager:
```bash
sudo cp pacman_toolkit/99-pacman-unbrick.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

**Note**: The udev rules set the `uucp` group for device access. Ensure your user is in this group:
```bash
sudo usermod -aG uucp $USER
# Log out and log back in for group changes to take effect
```

### 3. Download Firmware
1. Download the appropriate Nothing OS firmware from [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive)
2. Extract the firmware images
3. Place the required `.img` files in `pacman_toolkit/firmware/`

### 4. Install mtkclient (For MTK Mode)
If you need deep unbrick capability (MTK mode):
```bash
cd pacman_toolkit
git clone https://github.com/bkerler/mtkclient
cd mtkclient
pip install -r requirements.txt
pip install .
```

## 📖 Usage

### Quick Start

1. **Prepare the toolkit:**
```bash
cd pacman_toolkit
chmod +x pacman_interceptor.py flash_rescue.sh
```

2. **Start the interceptor:**
```bash
sudo ./pacman_interceptor.py
```
The script will display: `Waiting for Nothing Phone 2(a) (Pacman)...`

3. **Connect the device:**
   - Force shutdown: Hold **Vol+ and Power** until screen goes black
   - Enter recovery mode: Immediately switch to holding **Vol+ and Vol- and Power**
   - Connect USB cable while holding the buttons
   - Watch the terminal for status messages

4. **Automatic recovery:**
   - If **Fastboot** detected: Script sends freeze command and flashes automatically
   - If **MTK BROM** detected: Script triggers mtkclient payload and flashes critical partitions
   - Wait for "Rescue Complete" message

5. **Post-recovery:**
   - Disconnect USB cable
   - Hold **Vol+ and Power** to enter Fastboot Mode
   - Device should now boot normally or be ready for full firmware restoration

## 🔧 Troubleshooting

### Device Not Detected
- Check USB cable (try a different cable)
- Try a different USB port (USB 2.0 ports often work better)
- Monitor USB events: `dmesg -w`
- Verify udev rules are loaded: `udevadm control --reload-rules`

### "Resource Busy" Error in Fastboot
- Kill other ADB/Fastboot instances: `killall adb; killall fastboot`
- Ensure ModemManager isn't interfering (udev rules should prevent this)
- The script automatically detaches kernel drivers, but verify no other tools are accessing the device

### mtkclient Fails
- Ensure you have the latest mtkclient: `cd mtkclient && git pull`
- Verify Dimensity 7200 (MT6886) support in mtkclient
- Try manual payload: `python mtkclient/mtk payload` before connecting device
- Check that Python dependencies are installed: `pip install -r requirements.txt`

### Max Retries Exceeded
- Device bootloop window may be too short
- Try holding the button combination longer
- Ensure USB connection is stable (try different cable/port)
- Verify USB permissions and that your user is in the `uucp` group (see Installation step 2)

### Firmware Files Missing
```bash
# Verify firmware files exist
ls -la pacman_toolkit/firmware/
```
The flash script validates all required files before starting operations.

### Detailed Logs
For advanced troubleshooting, check the console output. The interceptor now provides detailed error tracking and device identification logs (VID:PID:BUS:ADDR) to help diagnose connection issues or driver conflicts.

## ⚠️ Important Warnings

- **BACKUP YOUR DATA**: This process may result in data loss
- **USE OFFICIAL FIRMWARE**: Only use firmware from trusted sources like [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive)
- **BATTERY LEVEL**: Ensure device has at least 50% battery before starting
- **DO NOT DISCONNECT**: Never disconnect the device during flashing operations
- **REGION MATCH**: Use firmware matching your device's region
- **WARRANTY**: This process may void your warranty

## 📁 Project Structure

```
Nothing-Phone-2-a-/
├── README.md                              # This file
├── PROTOCOL.md                            # Detailed technical protocol documentation
├── pacman_toolkit/
│   ├── pacman_interceptor.py             # USB interception and device detection script
│   ├── flash_rescue.sh                   # Automated flashing script (Fastboot/MTK modes)
│   ├── 99-pacman-unbrick.rules           # Udev rules for USB permissions
│   └── firmware/                         # Place your firmware files here
│       ├── boot.img
│       ├── vbmeta.img
│       ├── preloader.img                 # (MTK mode only)
│       └── lk.img                        # (MTK mode only)
└── .gitignore
```

## 📚 Documentation

For detailed technical information about the unbrick protocol, USB timing, and implementation details, see [PROTOCOL.md](PROTOCOL.md).

## 🙏 Credits and References

- **Firmware Archive**: [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive)
- **mtkclient**: [bkerler/mtkclient](https://github.com/bkerler/mtkclient) - MediaTek bootloader exploit toolkit
- **Nothing Phone Community**: For testing and feedback

## 📜 License

This toolkit is provided as-is for educational and recovery purposes. Use at your own risk.

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to:
- Report bugs or issues
- Suggest improvements
- Share your unbrick success stories
- Contribute firmware extraction guides

## 💬 Support

If you encounter issues:
1. Check the [Troubleshooting](#-troubleshooting) section
2. Review [PROTOCOL.md](PROTOCOL.md) for technical details
3. Open an issue on GitHub with:
   - Your device model and region
   - Firmware version used
   - Full error logs from the interceptor script
   - Output from `dmesg` showing USB events

---

**⚡ Remember**: This toolkit is your last resort for unbricking. Always try official recovery methods first!
