# Device Optimizer

A safe, honest command-line tool for Windows, macOS, and Linux.

- `report`: CPU, memory, disk, uptime, top resource users, startup items, and advice
- `clean`: removes old temp/cache files (dry run by default)

## Run from source
    pip install -r requirements.txt
    python device_optimizer.py report
    python device_optimizer.py clean            # preview only
    python device_optimizer.py clean --apply    # actually delete
    python device_optimizer.py clean --days 30  # only files 30+ days old

## Get the executable
Pushing to `main` builds Windows, macOS, and Linux executables via GitHub Actions
(see the Actions tab, then Artifacts). Create a release with a tag like `v1.0`
to attach them to a downloadable Release.

On Windows you can also build locally by double-clicking `build_exe.bat`.

Run the exe from a terminal, e.g. `device_optimizer-windows.exe report`.
Unsigned executables may trigger a Windows SmartScreen warning; choose
"More info" then "Run anyway".
