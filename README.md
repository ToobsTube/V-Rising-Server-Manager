# V Rising Server Manager

A lightweight GUI for managing your V Rising dedicated server on Windows.

**Version 1.0.0** · By [ToobsTube]

Also available as a standalone exe on [Nexus Mods](https://www.nexusmods.com) — no Python required.

---

## Overview

V Rising Server Manager gives server owners a clean, simple interface for everything that normally requires digging through config files, task scheduler, and command prompts. Start, stop, and monitor your server, schedule restarts with in-game warnings, run automated backups, and tweak common game settings — all from one window.

---

## Versions

This repository contains the Python source. Two versions are available:

- **Standalone exe** — Packages everything into a single executable. No Python installation required. Recommended for most people.
- **Python script (this repo)** — Run `vrising_manager.py` directly if you already have Python installed or want to inspect, fork, or modify the code.

Both versions are identical in features.

---

## Requirements

### Standalone exe
- Windows 10 or 11
- A V Rising dedicated server installation (via Steam or SteamCMD)
- Nothing else

### Python script
- Windows 10 or 11
- Python 3.8 or newer
- `psutil` package — install with `pip install psutil`
- A V Rising dedicated server installation (via Steam or SteamCMD)

---

## Running from source

```bash
pip install psutil
python vrising_manager.py
```

---

## First Launch

On first launch the app opens to the **Setup tab** where you can point it at your existing server installation, or follow the steps to download and install a fresh one using the built-in SteamCMD integration. Your settings are saved automatically from that point on.

> **Note for exe users:** Windows may show a SmartScreen warning the first time because the exe is not code-signed. Click **"More info"** then **"Run anyway"** to proceed. This is normal for unsigned community tools.

**Multiple servers?** The manager supports profiles — create a separate profile for each server instance and switch between them from the title bar. Each profile saves its own settings independently. You can also run multiple copies of the manager at the same time, one per server, so you can monitor and control all of them without switching back and forth.

---

## Features

### Server Control
Start and stop your server with a single button. The status bar shows live CPU and memory usage while the server is running.

### Game Settings
Edit the most commonly changed server settings — player limits, PvP toggle, day/night cycle length, XP and resource multipliers, castle decay, and more — without opening a config file. Changes take effect the next time the server starts.

### Scheduled Restart
Schedule a server restart or maintenance shutdown with automatic in-game announcements. Players receive warnings at 10, 5, 2, and 1 minute before the server stops.

The **Restart after shutdown** checkbox controls what happens when the countdown finishes. Leave it checked for a normal restart. Uncheck it when you need time to install mods, update server files, or perform maintenance before bringing the server back up — the server shuts down and waits for you to start it again manually.

### Daily Auto-Restart
Set a time for the server to restart automatically every day. Can be enabled or disabled at any time.

### Automated Backups
Back up your world save on demand or on a schedule. Supports any local drive, network drive, or cloud-synced folder (OneDrive, Google Drive, Dropbox, etc.). Configure how often backups run and how many to keep.

### Themes
Five built-in color themes: Dark Blue (default), Dark Green, Dark Red, Midnight Purple, and Light.

---

## Notes

- In-game announcements require RCON to be enabled in your server settings.
- Game setting changes are saved immediately but only take effect on the next server start.
- When you close the manager while the server is running, you'll be asked whether to shut the server down or leave it running. The server itself does not depend on the manager to stay open.
- The backup feature copies whatever the server has most recently saved to disk.

---

## Version History

| Version | Notes |
|---------|-------|
| 1.0.0 | Initial release |

---

*Created by [ToobsTube](https://www.nexusmods.com/profile/ToobsTube) · Not affiliated with Stunlock Studios*
