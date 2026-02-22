# Step-by-Step Guide: Unbricking Nothing Phone 2(a)

This guide provides a single, linear set of instructions to unbrick your Nothing Phone 2(a) (Pacman) using this toolkit. Follow these steps exactly to avoid confusion.

## 📋 Phase 1: Preparation (Do this first)

### 1. Check Your Environment
Ensure you are running **Arch Linux**. This toolkit is optimized for Arch due to its low-latency USB handling.
- Open a terminal.
- Run `uname -a` to confirm your kernel version.
- Ensure you have root access (`sudo`).

### 2. Install Required Packages
Run the following commands to install necessary dependencies:
```bash
sudo pacman -Syu
sudo pacman -S base-devel git python python-pip libusb android-tools python-pyusb python-libusb1
```

### 3. Clone the Repository
Download the toolkit to your machine:
```bash
git clone https://github.com/DaRipper91/Nothing-Phone-2-a-.git
cd Nothing-Phone-2-a-
```

### 4. Set Up Permissions (Udev Rules)
This step is crucial for the toolkit to access your device without interference.
```bash
# Copy the rules file
sudo cp pacman_toolkit/99-pacman-unbrick.rules /etc/udev/rules.d/

# Reload the rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Add your user to the uucp group (replace $USER with your username if needed)
sudo usermod -aG uucp $USER
```
*Tip: Log out and log back in for group changes to take full effect.*

---

## ⬇️ Phase 2: Firmware Setup (Crucial Step)

You must download and prepare the correct firmware files.

### 1. Download Firmware
- Go to the [Nothing Archive](https://github.com/spike0en/nothing_archive).
- Find **Phone (2a) - Pacman**.
- Download the latest **OTA Images** (click "Here").
- Download both `Pacman_...-image-boot.7z` and `Pacman_...-image-firmware.7z`.

### 2. Create Firmware Directory
Inside the `pacman_toolkit` folder, create a `firmware` directory:
```bash
mkdir -p pacman_toolkit/firmware/
```

### 3. Extract and Move Files
Extract the downloaded `.7z` files. You need to move specific files into `pacman_toolkit/firmware/`.

**Required Files:**
1.  From the `boot` archive:
    -   `boot.img` -> `pacman_toolkit/firmware/boot.img`
    -   `vbmeta.img` -> `pacman_toolkit/firmware/vbmeta.img`
2.  From the `firmware` archive (for deep unbrick):
    -   `preloader_raw.img` -> `pacman_toolkit/firmware/preloader.img` **(RENAME THIS!)**
    -   `lk.img` (or `lk`) -> `pacman_toolkit/firmware/lk.img`

**⚠️ VERIFY FILE NAMES:**
Your `pacman_toolkit/firmware/` folder MUST contain:
- `boot.img`
- `vbmeta.img`
- `preloader.img` (NOT `preloader_raw.img`)
- `lk.img`

---

## 🔧 Phase 3: MTK Client Setup (Optional but Recommended)

If your device is completely dead (black screen, no fastboot), you need this.

```bash
cd pacman_toolkit
git clone https://github.com/bkerler/mtkclient
cd mtkclient
pip install -r requirements.txt
pip install .
cd ..  # Return to pacman_toolkit directory
```

---

## 🚀 Phase 4: The Rescue Operation

### 1. Run the Interceptor
Start the tool. It will wait for your device connection.
```bash
# Make sure you are in the pacman_toolkit directory
chmod +x pacman_interceptor.py flash_rescue.sh
sudo ./pacman_interceptor.py
```
You should see: `Waiting for Nothing Phone 2(a) (Pacman)...`

### 2. Connect Your Device
Follow this exact sequence to catch the bootloop window:

1.  **Force Power Off**: Hold **Vol+** and **Power** buttons until the screen is black.
2.  **Prepare Mode**: Immediately switch to holding **Vol+**, **Vol-**, and **Power** (all three buttons).
3.  **Connect**: Plug in the USB cable while keeping the buttons held.
4.  **Watch the Screen**:
    -   If the tool says "Device frozen", it caught Fastboot.
    -   If the tool says "Triggering mtkclient", it caught MTK mode.

### 3. Wait for Completion
The script will automatically flash the necessary partitions.
-   Wait for the message **"Rescue Complete"**.

---

## ✅ Phase 5: Post-Rescue

1.  Disconnect the USB cable.
2.  Hold **Vol+** and **Power** to boot into Fastboot Mode.
3.  If you see the Fastboot screen, congratulations! Your device is unbricked.
4.  You can now flash the full stock firmware using standard Fastboot commands if needed.

## 🆘 Troubleshooting

-   **"Resource Busy"**: Run `killall adb` and `killall fastboot` in another terminal.
-   **Device Not Detected**: Try a USB 2.0 port or a different cable. Check `dmesg -w` to see if the system detects the USB connection.
-   **MTK Client Error**: Ensure you installed `mtkclient` correctly in Phase 3.
