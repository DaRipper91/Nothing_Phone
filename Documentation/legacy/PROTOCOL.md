> **⚠️ MOVED**: This document has been integrated into the [Master Manual](../MASTER_MANUAL.md). Please refer to **Chapter 2** of the Master Manual for the most up-to-date instructions.

# Pacman Unbrick Protocol: Nothing Phone 2(a) [A142]
## Definitive Zero-Latency Recovery Toolkit

**Target Device**: Nothing Phone 2(a) (Codename: Pacman)
**SoC**: MediaTek Dimensity 7200 Pro (MT6886)
**Host**: Arch Linux

---

### 1. Arch Linux Environmental Prep

To achieve sub-500ms latency, we utilize a minimal Arch Linux environment with direct kernel access.

#### Dependencies
Install the required packages. We use `android-udev` for base rules and `python-pyusb` for the interceptor.

```bash
sudo pacman -Syu
sudo pacman -S base-devel git python python-pip libusb android-tools python-pyusb python-libusb1
```

#### Toolkit Setup
Clone or create the toolkit directory structure:

```bash
# Create directory
mkdir -p ~/pacman_recovery/toolkit/firmware

# Copy the provided scripts into ~/pacman_recovery/toolkit/
# - pacman_interceptor.py
# - flash_rescue.sh
# - 99-pacman-unbrick.rules
```

#### Udev Rules (The "Interceptor" Setup)
We bypass `ModemManager` latency and grant immediate permissions. Copy the rule file to `/etc/udev/rules.d/`.

```bash
sudo cp ~/pacman_recovery/toolkit/99-pacman-unbrick.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```

---

### 2. Firmware Acquisition

You must download the correct firmware for your region (Nothing OS).
Source: [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive)

1. Download the **Fastboot ROM** or extract `payload.bin` from the OTA zip (using `payload-dumper-go`).
2. Place the following files in `~/pacman_recovery/toolkit/firmware/`:
   - `preloader.img` (Vital for unbricking)
   - `lk.img` (Little Kernel / Bootloader)
   - `boot.img` (Kernel)
   - `vbmeta.img` (Verified Boot Metadata)

---

### 3. The Interceptor Script

The `pacman_interceptor.py` is the "God-Tier" catcher. It polls the USB bus directly to catch the device within the 500ms bootloop window.

- **Fastboot Detection**: If the device enters Fastboot (VID 0x18d1/0x2b4c), it immediately sends a raw USB command (`getvar:all`) to freeze the bootloader before it reboots, then launches the rescue flasher.
- **MTK Detection**: If the device enters BROM/Preloader (VID 0x0e8d), it triggers the `mtkclient` payload mechanism to bypass SLA and stabilize the device in Download Mode.

#### mtkclient Setup (Advanced)
For the MTK interception to work, you need `mtkclient`.

```bash
cd ~/pacman_recovery/toolkit
git clone https://github.com/bkerler/mtkclient
cd mtkclient
pip install -r requirements.txt
python setup.py build
python setup.py install
```

---

### 4. Execution Protocol

#### Step 1: Start the Interceptor
Run the interceptor script as root (for USB access consistency, though udev rules should allow user access).

```bash
cd ~/pacman_recovery/toolkit
chmod +x pacman_interceptor.py flash_rescue.sh
sudo ./pacman_interceptor.py
```

Output should indicate: `Waiting for Nothing Phone 2(a) (Pacman)...`

#### Step 2: The "Catch"
1. **Force Shutdown**: Hold **Vol+** and **Power** until the screen goes black.
2. **Enter Mode**: Immediately switch to holding **Vol+** and **Vol-** and **Power**.
3. **Plug In**: Connect the USB cable while holding the keys.
4. **Watch Terminal**:
   - If **Fastboot** is caught: Script will say "Device frozen" and flash automatically.
   - If **MTK** is caught: Script will say "Triggering mtkclient payload". Keep holding buttons until you see "Payload successful".

#### Step 3: Post-Flash
Once the script prints "Rescue Complete":
1. Disconnect USB.
2. Hold **Vol+** and **Power** to boot into Fastboot Mode.
3. If the device enters Fastboot, you have successfully unbricked. You can now flash the full system via standard tools.

---

### 5. Troubleshooting

- **"Resource Busy" in Fastboot**: The script handles detaching kernel drivers. Ensure no other `adb` or `fastboot` servers are running (`killall adb`).
- **mtkclient fails**: Ensure you are using the latest version of `mtkclient` which supports Dimensity 7200 (MT6886). If the automated payload fails, try running `python mtkclient/mtk payload` manually in a separate terminal *before* plugging in the device, while the interceptor is stopped.
- **Device not appearing**: Check `dmesg -w` to see if the cable is faulty or the port is suspending.
