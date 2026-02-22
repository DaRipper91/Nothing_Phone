# Firmware Acquisition Guide for Nothing Phone 2(a)

This guide provides step-by-step instructions on how to obtain the correct firmware files required for unbricking your Nothing Phone 2(a) (Pacman) using the `pacman_toolkit`.

## 📋 Prerequisites

*   **Internet Access**: To download the firmware files.
*   **7-Zip** (Windows) or `p7zip` (Linux/macOS): To extract `.7z` archives.
*   **File Manager**: To organize and rename files.

## 🔍 Step 1: Identify Your Firmware Version

Ideally, you should match the firmware version currently installed on your device or use the latest available version for your region.

The Nothing Phone 2(a) typically has regional variants (though often the firmware is unified). Common regions include:
*   **Global (GLO)**
*   **Europe (EEA)**
*   **India (IND)**

If you are unsure, the Global or EEA versions are often safe bets, but matching your original region is recommended.

## 🌐 Step 2: Navigate to the Firmware Archive

We use the [spike0en/nothing_archive](https://github.com/spike0en/nothing_archive) as the source for official firmware images.

1.  Open the [Nothing Archive Repository](https://github.com/spike0en/nothing_archive).
2.  Scroll down to the **Downloads** section.
3.  Look for **Nothing Phones** and then locate **Phone (2a) - Pacman**.

## ⬇️ Step 3: Download Firmware Files

1.  In the **Phone (2a) - Pacman** table, find the row corresponding to your desired **Nothing OS Version**.
2.  Look at the **OTA Images** column (the last column on the right).
3.  Click the **Here** link. This will take you to a release page (usually on GitHub Releases).
4.  On the release page, under **Assets**, download the following two files:
    *   `Pacman_...-image-boot.7z` (Contains `boot.img`, `vbmeta.img`, etc.)
    *   `Pacman_...-image-firmware.7z` (Contains `preloader`, `lk`, etc.)

    > **Note:** The filenames might vary slightly depending on the version, but look for `-image-boot.7z` and `-image-firmware.7z`.

## 📂 Step 4: Extract and Organize Files

1.  Create a folder named `firmware` inside your `pacman_toolkit` directory if it doesn't exist:
    ```bash
    mkdir -p pacman_toolkit/firmware/
    ```
2.  **Extract the `-image-boot.7z` archive**.
3.  **Extract the `-image-firmware.7z` archive**.

## 📝 Step 5: Select and Rename Files

You need specific files depending on your recovery mode. Move the following files to `pacman_toolkit/firmware/`.

### For Fastboot Mode (Standard Unbrick)

From the extracted **Boot** folder (`-image-boot`), copy:
*   `boot.img`
*   `vbmeta.img`

### For MTK Mode (Deep Unbrick / Dead Boot)

You need the Fastboot files **PLUS** critical bootloader files.

1.  From the extracted **Boot** folder (`-image-boot`), copy:
    *   `boot.img`
    *   `vbmeta.img`

2.  From the extracted **Firmware** folder (`-image-firmware`), copy:
    *   `preloader_raw.img` (or `preloader_raw`)
    *   `lk.img` (or `lk`)

3.  **⚠️ IMPORTANT: RENAME FILES**
    The toolkit expects specific filenames. You **must** rename the following files in `pacman_toolkit/firmware/`:

    *   Rename `preloader_raw.img` (or `preloader_raw`) -> **`preloader.img`**
    *   Rename `lk` (if it lacks an extension) -> **`lk.img`**

## ✅ Verification

Your `pacman_toolkit/firmware/` folder should look like this:

**For Fastboot Mode:**
```
pacman_toolkit/firmware/
├── boot.img
└── vbmeta.img
```

**For MTK Mode:**
```
pacman_toolkit/firmware/
├── boot.img
├── lk.img          <-- Renamed from lk or lk.bin
├── preloader.img   <-- Renamed from preloader_raw.img
└── vbmeta.img
```

Once the files are in place, you are ready to run the unbrick tool!
