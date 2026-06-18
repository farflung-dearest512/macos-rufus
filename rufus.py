#!/usr/bin/env python3
"""macos-rufus: create bootable Windows USB drives on macOS."""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    FileSizeColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TransferSpeedColumn,
)
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich import print as rprint

console = Console()

FAT32_LIMIT = 4 * 1024 ** 3  # 4 GiB


# ── helpers ──────────────────────────────────────────────────────────────────

def run(cmd: list[str], check=True, capture=True, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        capture_output=capture,
        text=True,
        **kw,
    )


def escalate_to_root():
    """Re-exec the script under sudo if not already root — prompts for password automatically."""
    if os.geteuid() != 0:
        console.print("[dim]Root access required — you may be prompted for your password.[/dim]")
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)


def _brew_path() -> str | None:
    return shutil.which("brew")


def _install_wimlib():
    brew = _brew_path()
    if not brew:
        console.print(
            "[red]Homebrew not found.[/red] "
            "Install Homebrew first: [bold]https://brew.sh[/bold]\n"
            "Then run: [bold]brew install wimlib[/bold]"
        )
        sys.exit(1)
    console.print("[yellow]Installing wimlib via Homebrew...[/yellow]")
    # brew must run as the original user, not root — get login user
    login_user = os.environ.get("SUDO_USER") or os.environ.get("USER", "")
    if login_user and os.geteuid() == 0:
        subprocess.run(["sudo", "-u", login_user, brew, "install", "wimlib"], check=True)
    else:
        subprocess.run([brew, "install", "wimlib"], check=True)
    if not shutil.which("wimlib-imagex"):
        console.print("[red]wimlib install failed. Install manually: brew install wimlib[/red]")
        sys.exit(1)
    console.print("[green]wimlib installed.[/green]")


def check_deps():
    missing_critical = []
    for tool in ("hdiutil", "diskutil", "rsync"):
        if not shutil.which(tool):
            missing_critical.append(tool)
    if missing_critical:
        console.print(f"[red]Missing required macOS tools: {', '.join(missing_critical)}[/red]")
        sys.exit(1)

    if not shutil.which("wimlib-imagex"):
        console.print(
            "[yellow]wimlib-imagex not found[/yellow] — needed for Windows 11 ISOs (install.wim > 4 GiB)."
        )
        if Confirm.ask("Auto-install wimlib via Homebrew now?", default=True):
            _install_wimlib()
        else:
            console.print(
                "[dim]Skipping. If install.wim > 4 GiB the copy step will fail.[/dim]"
            )


# ── ISO ───────────────────────────────────────────────────────────────────────

def ask_iso_path() -> Path:
    while True:
        raw = Prompt.ask("\n[bold cyan]Path to Windows ISO[/bold cyan]").strip()
        raw = raw.strip("'\"")  # handle drag-drop quoting
        p = Path(raw).expanduser().resolve()
        if not p.exists():
            console.print(f"[red]Not found:[/red] {p}")
            continue
        if p.suffix.lower() != ".iso":
            console.print("[yellow]Warning: file doesn't end in .iso — continuing anyway.[/yellow]")
        return p


def mount_iso(iso: Path) -> str:
    """Mount ISO with hdiutil, return mount point."""
    console.print(f"\n[dim]Mounting {iso.name}...[/dim]")
    result = run(["hdiutil", "attach", "-nobrowse", "-readonly", str(iso)])
    # last line of output contains mount point
    for line in reversed(result.stdout.strip().splitlines()):
        parts = line.split("\t")
        if len(parts) >= 3 and parts[-1].strip().startswith("/"):
            return parts[-1].strip()
    raise RuntimeError(f"Could not parse mount point from hdiutil output:\n{result.stdout}")


def unmount_iso(mount_point: str):
    run(["hdiutil", "detach", mount_point, "-force"], check=False)


# ── USB detection ─────────────────────────────────────────────────────────────

def list_usb_drives() -> list[dict]:
    """Return list of external disk dicts via diskutil list -plist."""
    result = run(["diskutil", "list", "-plist", "external", "physical"])
    import plistlib
    data = plistlib.loads(result.stdout.encode())
    disks = []
    for dev in data.get("WholeDisks", []):
        info_result = run(["diskutil", "info", "-plist", dev])
        info = plistlib.loads(info_result.stdout.encode())
        disks.append({
            "node": f"/dev/{dev}",
            "name": info.get("MediaName", "Unknown"),
            "size": info.get("TotalSize", 0),
            "protocol": info.get("BusProtocol", "?"),
        })
    return disks


def fmt_size(b: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PB"


def ask_usb(drives: list[dict]) -> dict:
    table = Table(title="Detected USB Drives", show_lines=True)
    table.add_column("#", style="bold cyan", width=3)
    table.add_column("Device", style="bold")
    table.add_column("Name")
    table.add_column("Size", justify="right")
    table.add_column("Bus")

    for i, d in enumerate(drives, 1):
        table.add_row(str(i), d["node"], d["name"], fmt_size(d["size"]), d["protocol"])

    console.print()
    console.print(table)

    while True:
        raw = Prompt.ask("[bold cyan]Select USB drive number[/bold cyan]")
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(drives):
                return drives[idx]
        except ValueError:
            pass
        console.print(f"[red]Enter a number between 1 and {len(drives)}.[/red]")


# ── disk prep ─────────────────────────────────────────────────────────────────

def unmount_disk_partitions(disk_node: str):
    run(["diskutil", "unmountDisk", disk_node], check=False)


def format_usb(disk_node: str):
    """Erase USB as FAT32 with MBR scheme — broadest UEFI + BIOS compat."""
    console.print(f"\n[yellow]Erasing {disk_node} as FAT32 (MBR)...[/yellow]")
    run(
        [
            "diskutil", "eraseDisk", "FAT32", "WINUSB",
            "MBRFormat", disk_node,
        ],
        capture=False,
    )


def get_volume_path(disk_node: str) -> Path:
    """Return /Volumes/... path for first partition of disk."""
    import plistlib
    result = run(["diskutil", "info", "-plist", disk_node + "s1"])
    info = plistlib.loads(result.stdout.encode())
    mp = info.get("MountPoint", "")
    if not mp:
        raise RuntimeError(f"Could not find mount point for {disk_node}s1")
    return Path(mp)


# ── file copy ─────────────────────────────────────────────────────────────────

def get_wim_path(mount_point: str) -> Path | None:
    candidates = [
        Path(mount_point) / "sources" / "install.wim",
        Path(mount_point) / "sources" / "install.esd",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def copy_files_except_wim(src: str, dst: Path):
    console.print("\n[dim]Copying boot files (excluding install.wim)...[/dim]")
    run(
        [
            "rsync", "-a", "--progress",
            "--exclude=sources/install.wim",
            "--exclude=sources/install.esd",
            f"{src}/",
            str(dst) + "/",
        ],
        capture=False,
    )


def split_and_copy_wim(wim_path: Path, dst: Path):
    """Split install.wim into FAT32-safe chunks and copy."""
    if not shutil.which("wimlib-imagex"):
        raise RuntimeError(
            "install.wim is > 4 GiB but wimlib-imagex is not installed.\n"
            "Run: brew install wimlib"
        )
    out_dir = dst / "sources"
    out_dir.mkdir(parents=True, exist_ok=True)
    swm_prefix = str(out_dir / "install.swm")
    console.print(
        f"\n[yellow]install.wim is > 4 GiB — splitting into .swm chunks...[/yellow]"
    )
    run(
        ["wimlib-imagex", "split", str(wim_path), swm_prefix, "3800"],
        capture=False,
    )


def copy_wim_direct(wim_path: Path, dst: Path):
    dst_sources = dst / "sources"
    dst_sources.mkdir(parents=True, exist_ok=True)
    dst_file = dst_sources / wim_path.name
    console.print(f"\n[dim]Copying {wim_path.name} ({fmt_size(wim_path.stat().st_size)})...[/dim]")
    run(["rsync", "-ah", "--progress", str(wim_path), str(dst_file)], capture=False)


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    console.print(
        Panel(
            "[bold white]macos-rufus[/bold white]  —  Windows bootable USB creator",
            subtitle="macOS · UEFI/BIOS · FAT32",
            style="bold blue",
        )
    )

    escalate_to_root()
    check_deps()

    # 1. ISO
    iso_path = ask_iso_path()

    # 2. USB
    drives = list_usb_drives()
    if not drives:
        console.print("[red]No external USB drives detected. Plug one in and retry.[/red]")
        sys.exit(1)

    selected = ask_usb(drives)
    disk_node = selected["node"]

    # 3. Confirm — destructive
    console.print(
        f"\n[bold red]WARNING:[/bold red] "
        f"[white]{disk_node}[/white] ([yellow]{selected['name']}[/yellow], "
        f"{fmt_size(selected['size'])}) will be [bold red]completely erased[/bold red]."
    )
    if not Confirm.ask("[bold]Proceed?[/bold]", default=False):
        console.print("Aborted.")
        sys.exit(0)

    mount_point = None
    try:
        # 4. Mount ISO
        mount_point = mount_iso(iso_path)
        console.print(f"[green]ISO mounted at:[/green] {mount_point}")

        # 5. Format USB
        unmount_disk_partitions(disk_node)
        format_usb(disk_node)

        usb_volume = get_volume_path(disk_node)
        console.print(f"[green]USB volume:[/green] {usb_volume}")

        # 6. Copy files
        wim_path = get_wim_path(mount_point)
        copy_files_except_wim(mount_point, usb_volume)

        if wim_path:
            size = wim_path.stat().st_size
            if size > FAT32_LIMIT:
                split_and_copy_wim(wim_path, usb_volume)
            else:
                copy_wim_direct(wim_path, usb_volume)
        else:
            console.print("[yellow]No install.wim/install.esd found — ISO may be unusual.[/yellow]")

        # 7. Flush
        console.print("\n[dim]Flushing writes...[/dim]")
        run(["diskutil", "unmountDisk", disk_node], check=False)

        console.print(
            Panel(
                f"[bold green]Done![/bold green]\n\n"
                f"Bootable Windows USB ready on [white]{disk_node}[/white].\n"
                f"Eject and boot target machine via UEFI/BIOS boot menu.",
                style="green",
            )
        )

    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    finally:
        if mount_point:
            console.print(f"[dim]Unmounting ISO...[/dim]")
            unmount_iso(mount_point)


if __name__ == "__main__":
    main()
