# V Rising Server Manager

A lightweight GUI for managing your V Rising dedicated server on Windows.

**Version 1.1.4** · By [ToobsTube]

Also available as a standalone exe — no Python required.

---

## Overview

V Rising Server Manager gives server owners a clean, simple interface for everything that normally requires digging through config files, task scheduler, and command prompts. Start, stop, and monitor your server, schedule restarts with in-game warnings, run automated backups, and tweak common game settings — all from one window.

---

## Versions

This repository contains the Python source. Two versions are available:

- **Standalone exe** — Packages everything into a single executable. No Python installation required. Recommended for most people.
- **Python script** — Run `vrising_manager.py` directly if you already have Python installed or want to inspect, fork, or modify the code.

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

Stopping is graceful: the manager asks the server to shut down the same way pressing Ctrl+C in its console does, so V Rising saves the world first and players log back in where they left. The status bar shows the save in progress. Only if the server hasn't closed after 2 minutes is it force-stopped, and the manager warns you that the world may not have saved. Scheduled restarts, the daily restart and server updates all stop the server this way.

### Connection Check
On the **Network** tab. Shows your local IP and your public IP, with a button to copy each as `IP:Port` for Direct Connect. The public IP stays hidden unless you click **Show**, and **Copy** works without showing it, so it's safe to use while streaming.

**Run Connection Check** tests that the server is answering (and shows its name, players and version), how quickly it answers through your public address, and whether Steam's server list has it. Each result explains what to do if something's wrong.

> **Playing from the same house as the server?** Many home routers can't connect back to their own public address. Your server may then look high-latency, or be hidden by the server list's **Latency** filter, and Direct Connect to the public IP may fail. Loosen the Latency filter, or Direct Connect to the server PC's **local** IP (use the Copy button next to it) with **LAN Server** left unticked. That box is only for servers running in LAN mode. Players outside your home aren't affected.

### Game Settings
Edit the most commonly changed server settings — player limits, PvP toggle, day/night cycle length, XP and resource multipliers, castle decay, and more — without opening a config file. Changes take effect the next time the server starts.

### Scheduled Restart
Schedule a server restart or maintenance shutdown with automatic in-game announcements. Players receive warnings at 10, 5, 2, and 1 minute before the server stops.

The **Restart after shutdown** checkbox controls what happens when the countdown finishes. Leave it checked for a normal restart. Uncheck it when you need time to install mods, update server files, or perform maintenance before bringing the server back up — the server shuts down and waits for you to start it again manually.

### Automatic Restart
Set a time for the server to restart automatically, **every day** or once a week on the day you pick. Can be enabled or disabled at any time. If the server is already stopped at that time, the restart is skipped without sending warnings, and the tab notes whether it was stopped from the manager or may have crashed. **Skip if up < (h)** (default 10) also skips it when the server was started less than that many hours before, for example after you restarted it yourself in the evening; set it to 0 to always restart.

### Automated Backups
Back up your world save on demand or on a schedule. Supports any local drive, network drive, or cloud-synced folder (OneDrive, Google Drive, Dropbox, etc.). Configure how often backups run and how many to keep.

### Themes
Five built-in color themes: Dark Blue (default), Dark Green, Dark Red, Midnight Purple, and Light.

---

## Notes

- In-game announcements require RCON to be enabled in your server settings.
- Game setting changes are saved immediately but only take effect on the next server start.
- Server settings, the admin list and the ban list are kept in `<server folder>\save-data\Settings`, which game updates never touch. If yours are still in the game's default `VRisingServer_Data\StreamingAssets\Settings` folder, which updates do replace, the manager copies them over the first time it saves, keeping anything you set by hand.
- When you close the manager while the server is running, you'll be asked whether to shut the server down or leave it running. The server itself does not depend on the manager to stay open.
- The backup feature copies whatever the server has most recently saved to disk.

---

## Enabling RCON

RCON is required for in-game announcements (restart warnings). Without it the manager will still start, stop, and monitor your server — you just won't get the countdown messages sent to players.

To enable RCON, open your server's `ServerHostSettings.json` file. It's located in your server's `Settings` folder:

```
<server folder>\save-data\Settings\ServerHostSettings.json
```

Find the `Rcon` section and set these three values:

```json
"Rcon": {
  "Enabled": true,
  "Password": "your_password_here",
  "Port": 25575
}
```

- **Enabled** — must be `true`
- **Password** — set something reasonably strong; this is how the manager authenticates
- **Port** — `25575` is the default; change it only if something else is using that port

Enter the same password and port in the manager's **Setup tab** under the RCON section. Changes take effect the next time the server starts.

---

## Version History

| Version | Notes |
|---------|-------|
| 1.1.4 | The automatic restart can run every day or once a week on a chosen day · Turning it off and on again quickly can no longer leave two restart timers running (which restarted the server twice) · The daily restart no longer sends warnings or shows RCON errors when the server is already stopped; it skips quietly and says why (stopped from the manager, or possibly crashed) · New **Skip if up < (h)** setting (default 10): the daily restart is skipped when the server was started only a few hours before it · The Daily Restart tab keeps showing how the last restart went |
| 1.1.3 | The Direct Connect tips now say to leave **LAN Server** unticked (it's only for servers in LAN mode) · Installing or updating the server shows how much SteamCMD has written while its own messages are held back, instead of looking frozen · A fresh SteamCMD install now finishes in one click (it re-runs SteamCMD after it updates itself) · Two servers on one PC can no longer be mixed up when one folder name starts with the other (for example `VRisingServer` and `VRisingServer-Test`) |
| 1.1.2 | Preset dropdowns list the game's real presets, read from your server (Game Settings Preset and a new Difficulty Preset), and default to blank · The old made-up preset names are cleared automatically · The All Waypoints Unlocked tooltip explains that waypoints only show on the map once their area is explored |
| 1.1.1 | The mouse wheel scrolls a tab wherever the pointer is, not just over empty background · Scrolling over a number box or dropdown no longer changes its value · Server settings, admin list and ban list are kept in `save-data\Settings` (moved there automatically), so game updates can't reset them |
| 1.1.0 | Stopping the server now saves the world first (also for scheduled, daily and update restarts) · New Connection Check on the Network tab · The exe now keeps its settings in its own folder · Version shown in the window |
| 1.0.0 | Initial release |

---

*Created by [ToobsTube] · Not affiliated with Stunlock Studios*
