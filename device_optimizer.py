#!/usr/bin/env python3
"""
device_optimizer.py - honest, safe device optimizer (Windows / macOS / Linux)

Usage:
  python device_optimizer.py report            # health snapshot + advice
  python device_optimizer.py clean             # DRY RUN: shows what would be deleted
  python device_optimizer.py clean --apply     # actually deletes old temp/cache files
  python device_optimizer.py clean --days 14   # only files untouched for 14+ days

Requires: pip install psutil
"""
import argparse
import os
import platform
import sys
import tempfile
import time
from pathlib import Path

try:
    import psutil
except ImportError:
    sys.exit("Missing dependency. Run:  pip install psutil")

SYSTEM = platform.system()  # 'Windows', 'Darwin', 'Linux'


def fmt(n):
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} PB"


# ----------------------------------------------------------------- report
def startup_items():
    items = []
    if SYSTEM == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run")
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    items.append(name)
                    i += 1
                except OSError:
                    break
        except OSError:
            pass
    elif SYSTEM == "Darwin":
        d = Path.home() / "Library/LaunchAgents"
        if d.exists():
            items = [p.name for p in d.glob("*.plist")]
    else:
        d = Path.home() / ".config/autostart"
        if d.exists():
            items = [p.name for p in d.glob("*.desktop")]
    return items


def report():
    print(f"=== Device report: {platform.node()} ({SYSTEM} {platform.release()}) ===\n")
    advice = []

    # warm up per-process CPU counters, then sample
    procs = list(psutil.process_iter(["name", "memory_info"]))
    for p in procs:
        try:
            p.cpu_percent(None)
        except psutil.Error:
            pass
    cpu = psutil.cpu_percent(interval=1.0)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage(Path.home().anchor or "/")
    uptime_days = (time.time() - psutil.boot_time()) / 86400

    print(f"CPU usage:  {cpu:.0f}%  ({psutil.cpu_count()} logical cores)")
    print(f"Memory:     {fmt(mem.used)} / {fmt(mem.total)} ({mem.percent:.0f}%)")
    print(f"Disk:       {fmt(disk.used)} / {fmt(disk.total)} ({disk.percent:.0f}%)")
    print(f"Uptime:     {uptime_days:.1f} days")

    battery = getattr(psutil, "sensors_battery", lambda: None)()
    if battery:
        print(f"Battery:    {battery.percent:.0f}%"
              f"{' (charging)' if battery.power_plugged else ''}")

    # top processes
    rows = []
    for p in procs:
        try:
            rows.append((p.info["name"] or "?",
                         p.info["memory_info"].rss,
                         p.cpu_percent(None)))
        except (psutil.Error, AttributeError):
            pass
    print("\nTop memory users:")
    for name, rss, _ in sorted(rows, key=lambda r: r[1], reverse=True)[:5]:
        print(f"  {name:<30} {fmt(rss)}")
    print("\nTop CPU users:")
    for name, _, c in sorted(rows, key=lambda r: r[2], reverse=True)[:5]:
        print(f"  {name:<30} {c:.0f}%")

    items = startup_items()
    print(f"\nStartup items ({len(items)}):")
    for it in items:
        print(f"  - {it}")

    # advice
    if mem.percent > 85:
        advice.append("Memory is nearly full: close heavy apps/browser tabs.")
    if disk.percent > 90:
        advice.append("Disk is almost full: free space (run 'clean', remove big unused files).")
    if uptime_days > 14:
        advice.append("Not restarted in 2+ weeks: a reboot often fixes slowness and applies updates.")
    if len(items) > 8:
        advice.append("Many startup items: disable ones you don't need for faster boot.")
    if cpu > 80:
        advice.append("CPU is busy: check the top CPU users above.")
    print("\nAdvice:")
    print("\n".join(f"  * {a}" for a in advice) if advice else "  * Looks healthy. Nothing urgent.")


# ------------------------------------------------------------------ clean
def clean_targets():
    dirs = [Path(tempfile.gettempdir())]
    home = Path.home()
    if SYSTEM == "Windows":
        dirs.append(Path(os.environ.get("LOCALAPPDATA", home)) / "Temp")
    elif SYSTEM == "Darwin":
        dirs += [home / "Library/Caches", home / "Library/Logs"]
    else:
        dirs.append(home / ".cache")
    seen, out = set(), []
    for d in dirs:
        try:
            r = d.resolve()
        except OSError:
            continue
        if r.exists() and r not in seen:
            seen.add(r)
            out.append(r)
    return out


def clean(apply, days):
    cutoff = time.time() - days * 86400
    mode = "DELETING" if apply else "DRY RUN (nothing will be deleted)"
    print(f"=== Cleanup: files not modified in {days}+ days | {mode} ===\n")
    grand_total, grand_count = 0, 0
    for root in clean_targets():
        total = count = errors = 0
        for dirpath, _, files in os.walk(root, followlinks=False):
            for f in files:
                path = os.path.join(dirpath, f)
                try:
                    st = os.lstat(path)
                    if os.path.islink(path) or st.st_mtime > cutoff:
                        continue
                    if apply:
                        os.remove(path)
                    total += st.st_size
                    count += 1
                except OSError:
                    errors += 1  # in use / no permission: skip safely
        print(f"{root}\n  {count} files, {fmt(total)}"
              f"{f'  ({errors} skipped)' if errors else ''}")
        grand_total += total
        grand_count += count
    verb = "Freed" if apply else "Could free"
    print(f"\n{verb} {fmt(grand_total)} across {grand_count} files.")
    if not apply and grand_count:
        print("Run again with --apply to delete them.")


def main():
    ap = argparse.ArgumentParser(description="Safe device health + cleanup tool")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("report", help="show system health and advice")
    c = sub.add_parser("clean", help="remove old temp/cache files")
    c.add_argument("--apply", action="store_true", help="actually delete (default is dry run)")
    c.add_argument("--days", type=int, default=7, help="min age of files in days (default 7)")
    args = ap.parse_args()
    if args.cmd == "report":
        report()
    else:
        clean(args.apply, args.days)


if __name__ == "__main__":
    main()
