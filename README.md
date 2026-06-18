# 🖥️ macos-rufus

> **The Rufus alternative for macOS** — create bootable Windows 10 / Windows 11 USB drives directly from your Mac, no VMs, no Boot Camp, no nonsense.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![macOS](https://img.shields.io/badge/macOS-12%2B-000000?style=flat-square&logo=apple&logoColor=white)](https://apple.com/macos)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)
[![Windows 10](https://img.shields.io/badge/Windows-10-0078D6?style=flat-square&logo=windows&logoColor=white)](https://microsoft.com)
[![Windows 11](https://img.shields.io/badge/Windows-11-0078D6?style=flat-square&logo=windows11&logoColor=white)](https://microsoft.com)

---

## 📌 What Is This?

**macos-rufus** is an open-source command-line tool for macOS that does exactly one thing, perfectly: it turns a Windows ISO file into a bootable USB drive.

If you've ever searched for:

- *"Rufus for Mac"*
- *"How to create bootable Windows USB on macOS"*
- *"Make Windows 11 bootable USB from Mac"*
- *"Rufus alternative macOS"*
- *"dd command Windows ISO Mac"* (hint: `dd` doesn't work for Windows ISOs)
- *"How to install Windows from a Mac"*

…you found the right tool.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Windows 10 & 11 support** | Tested with official Microsoft ISO files |
| **Handles install.wim > 4 GB** | Automatically splits oversized files using `wimlib` — the #1 cause of failure on other tools |
| **FAT32 + MBR format** | Maximum compatibility across UEFI and legacy BIOS systems |
| **Interactive USB picker** | Lists all connected USB drives with size and name — no guessing device paths |
| **Safe by design** | Requires `sudo`, shows explicit destructive-action warning, needs manual confirmation |
| **Beautiful terminal UI** | Powered by `rich` — progress bars, color, tables |
| **No dependencies on Rufus, VirtualBox, or Boot Camp** | Pure macOS + Python |
| **Drag-and-drop ISO path** | Drag your `.iso` file into the terminal — quoted paths handled automatically |

---

## 🚀 Quick Start

### 1. Prerequisites

Install [Homebrew](https://brew.sh) if you haven't already, then:

```bash
# Required for Windows 11 ISOs (install.wim > 4 GB)
brew install wimlib
```

> **Note:** `wimlib` is already a macOS native binary. No Wine, no emulation.

### 2. Clone the repo

```bash
git clone https://github.com/yourusername/macos-rufus.git
cd macos-rufus
```

### 3. Set up the Python virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4. Run it

```bash
sudo venv/bin/python3 rufus.py
```

> `sudo` is required because formatting a USB drive and writing to raw disk devices is a privileged operation on macOS.

---

## 📖 Step-by-Step Usage

```
╭─────────────────────────────────────────────────────╮
│  macos-rufus  —  Windows bootable USB creator       │
│               macOS · UEFI/BIOS · FAT32             │
╰─────────────────────────────────────────────────────╯
```

**Step 1 — Enter ISO path**

```
Path to Windows ISO: /Users/you/Downloads/Win11_23H2_English_x64.iso
```

You can also drag and drop the `.iso` file directly from Finder into your terminal window.

**Step 2 — Pick your USB drive**

```
┌───────────────────────────────────────────────────────────┐
│                    Detected USB Drives                    │
├───┬──────────────┬────────────────────┬────────┬─────────┤
│ # │ Device       │ Name               │   Size │ Bus     │
├───┼──────────────┼────────────────────┼────────┼─────────┤
│ 1 │ /dev/disk4   │ SanDisk Ultra USB  │ 32.0 GB│ USB     │
│ 2 │ /dev/disk5   │ Kingston DataTrav… │ 64.0 GB│ USB     │
└───┴──────────────┴────────────────────┴────────┴─────────┘

Select USB drive number: 1
```

**Step 3 — Confirm**

```
WARNING: /dev/disk4 (SanDisk Ultra USB, 32.0 GB) will be completely erased.
Proceed? [y/N]:
```

**Step 4 — Sit back**

The tool will:
1. Mount the ISO (read-only, via `hdiutil`)
2. Erase and format the USB as FAT32 + MBR
3. Copy all boot files via `rsync`
4. Detect if `install.wim` exceeds 4 GiB and automatically split it into `.swm` chunks
5. Flush writes and unmount everything cleanly

---

## ⚙️ How It Works (Technical)

### Why not just use `dd`?

Unlike Linux ISOs (which are hybrid ISOs that `dd` writes byte-for-byte), **Windows ISOs are not `dd`-compatible**. Writing a Windows ISO with `dd` to a USB drive produces a non-bootable result. You need to:

1. Format the USB with a proper partition table (MBR) and filesystem (FAT32)
2. Copy the ISO contents — not the ISO image itself
3. Deal with the UEFI boot sector (handled by the files inside the ISO: `bootmgr.efi`, `efi/boot/bootx64.efi`)

### The 4 GiB problem

FAT32 has a hard per-file limit of 4,294,967,295 bytes (~4 GiB). Windows 11's `install.wim` often exceeds this. Most tools fail silently here.

**macos-rufus** detects this automatically and uses `wimlib-imagex split` to break the WIM into 3,800 MB chunks named `install.swm`, `install2.swm`, etc. The Windows installer natively understands and reassembles split WIM files — no extra steps needed on the target machine.

### Partition scheme: MBR vs GPT

MBR + FAT32 is chosen deliberately:

- **UEFI systems** boot via `efi/boot/bootx64.efi` (present in all modern Windows ISOs) — works on FAT32 + MBR
- **Legacy BIOS systems** boot via the MBR boot code + `bootmgr` — requires MBR scheme
- GPT + FAT32 works on pure UEFI but breaks on BIOS — MBR is the safe default

### Tools used under the hood

| Tool | Source | Purpose |
|---|---|---|
| `hdiutil` | macOS built-in | Mount ISO as read-only volume |
| `diskutil` | macOS built-in | List disks, erase and format USB |
| `rsync` | macOS built-in | Copy files with progress |
| `wimlib-imagex` | Homebrew (`wimlib`) | Split install.wim > 4 GiB |
| `rich` | pip | Terminal UI |

---

## 🔧 Requirements

| Requirement | Version |
|---|---|
| macOS | 12 Monterey or later (tested on Ventura, Sonoma, Sequoia) |
| Python | 3.11+ |
| Homebrew | Any recent version |
| wimlib | Latest via `brew install wimlib` |
| USB drive | 8 GB minimum for Windows 10, 16 GB for Windows 11 |

---

## 📥 Getting the Windows ISO

Download official ISOs directly from Microsoft — no third-party sites needed:

- **Windows 11**: [microsoft.com/software-download/windows11](https://www.microsoft.com/software-download/windows11)
- **Windows 10**: [microsoft.com/software-download/windows10ISO](https://www.microsoft.com/software-download/windows10ISO)

> Tip: On macOS, Microsoft's page may redirect you to the Media Creation Tool (Windows-only). Open the page in Safari's developer tools, set the User Agent to a non-Windows browser, or use a browser extension to spoof your user agent — the direct ISO download link will then appear.

---

## ❓ Troubleshooting

### "No external USB drives detected"

- Make sure the drive is physically connected and recognized by macOS (it should appear in Finder or Disk Utility)
- Try a different USB port or cable
- Run `diskutil list` to verify macOS sees the drive

### "install.wim splitting fails"

- Run `brew install wimlib` and retry
- Ensure you have enough free disk space — the split happens in memory + on the USB

### "USB not booting on target machine"

1. Enter your machine's BIOS/UEFI boot menu (usually `F12`, `F2`, `Esc`, or `Del` on boot)
2. Look for the USB drive under **UEFI** boot entries (not legacy)
3. Disable **Secure Boot** if Windows Setup won't launch (can re-enable after installation)
4. For very old machines (pre-2012), enable **CSM / Legacy Boot**

### "Permission denied"

Run with `sudo`:
```bash
sudo venv/bin/python3 rufus.py
```

### "hdiutil: attach failed"

- Verify the ISO file is not corrupted — compare its SHA256 against Microsoft's published checksum
- Make sure the ISO isn't already mounted (check Finder sidebar or `diskutil list`)

---

## 🛠️ Project Structure

```
macos-rufus/
├── rufus.py          # Main CLI tool — all logic lives here
├── requirements.txt  # Python dependencies (just: rich)
├── venv/             # Python virtual environment (not committed)
└── README.md         # This file
```

---

## 🔒 Security & Safety

- **Only external physical disks** are listed as targets — internal drives are never shown
- **Explicit confirmation required** before any destructive operation
- **Read-only ISO mount** — the source ISO is never modified
- **`sudo` required** — the tool will not silently drop privileges or operate on disks without root

---

## 🤝 Contributing

Pull requests welcome. Focus areas:

- [ ] GPT + NTFS support for pure-UEFI installs (no 4 GiB limit)
- [ ] Progress bar for WIM split operation
- [ ] Auto-detect and verify ISO SHA256 against Microsoft checksums
- [ ] Support for Windows Server ISOs
- [ ] GUI wrapper (Tkinter or native macOS via PyObjC)

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgements

- [Rufus](https://rufus.ie) — the original Windows tool this is inspired by
- [wimlib](https://wimlib.net) — the open-source WIM library that makes Windows 11 USB creation possible on non-Windows systems
- [rich](https://github.com/Textualize/rich) — beautiful terminal output for Python

---

<p align="center">
  Made for every Mac user who just wants to install Windows without booting into a Windows machine first.
</p>

<p align="center">
  <strong>macos-rufus</strong> · Rufus for Mac · Bootable Windows USB · macOS ISO Tool
</p>
