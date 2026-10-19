"""
V Rising Server Manager
A lightweight GUI for managing your V Rising dedicated server.
Requires Python 3.x (Tkinter is built-in on Windows)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import subprocess
import threading
import os
import json
import time
import psutil
import socket
import struct
import shutil
import re
from datetime import datetime, timedelta

# ── Profile / config system ─────────────────────────────────────────────────
_SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR  = os.path.join(_SCRIPT_DIR, "vrising_profiles")
# Legacy single-file config — migrated automatically on first run
LEGACY_CONFIG = os.path.join(_SCRIPT_DIR, "vrising_manager_config.json")
# Tracks which profile is active across launches
_LAST_PROFILE_FILE = os.path.join(_SCRIPT_DIR, "vrising_last_profile.txt")

# CONFIG_FILE is set dynamically once a profile is chosen (see pick_profile / VRisingManager.__init__)
CONFIG_FILE = LEGACY_CONFIG   # fallback until profile is selected

DEFAULT_CONFIG = {
    "server_path": "",
    "server_name": "My V Rising Server",
    "max_players": 10,
    "pvp_enabled": False,
    "day_length_minutes": 720,
    "night_length_minutes": 180,
    "blood_moon_frequency": 0.17,
    "blood_moon_duration": 1.5,
    "castle_decay_rate": 1.0,
    "castle_blood_essence_drain": 1.0,
    "global_settings_preset": "Standard",
    "xp_multiplier": 1.0,
    "drop_table_modifier": 1.0,
    "resource_yield_modifier": 1.0,
    "starting_blood_essence": 100,
    "soul_shard_modifier": 1.0,
    "pvp_damage_modifier": 1.0,
    "teleport_bound_items": True,
    "blood_bound_equipment": True,
    "bat_bound_items": False,
    "can_loot_enemy_containers": True,
    "global_chat": True,
    "all_waypoints_unlocked": False,
    "clan_size": 4,
    "castle_relocation_enabled": True,
    "castle_relocation_cooldown": 10800,
    "castle_min_distance": 2,
    "free_castle_claim": False,
    "free_castle_raid": False,
    "free_castle_destroy": False,
    "inactivity_kill_enabled": True,
    "disconnected_dead_enabled": True,
    "disconnected_dead_timer": 60,
    "disconnect_sun_immunity": 300,
    "starting_level": 0,
    "pvp_player_wday_start": 20,
    "pvp_player_wday_end": 22,
    "pvp_player_wend_start": 20,
    "pvp_player_wend_end": 22,
    "pvp_castle_wday_start": 20,
    "pvp_castle_wday_end": 22,
    "pvp_castle_wend_start": 20,
    "pvp_castle_wend_end": 22,
    "pvp_protection_mode": "Medium",
    "death_container_permission": "Anyone",
    "inventory_drop_on_death": "Always",
    "siege_weapon_health": "Normal",
    "announce_siege_spawn": True,
    "show_siege_icon": False,
    "war_event_interval": 0,
    "relic_spawn_type": "Unique",
    "servant_convert_rate": 1.0,
    "day_time_start": 9.0,
    "day_time_end": 17.0,
    "password": "",
    "game_port": 9876,
    "query_port": 9877,
    "auto_save_interval": 120,
    "auto_save_count": 20,
    "server_fps": 30,
    "max_admins": 4,
    "compress_saves": True,
    "list_steam": True,
    "list_eos": False,
    "secure": True,
    "description": "",
    "save_name": "world1",
    "rcon_enabled": False,
    "rcon_port": 25575,
    "rcon_password": "",
    "backup_dest": "",
    "theme": "Dark Blue (Default)",
    "backup_sched_enabled": False,
    "backup_interval_hours": 6,
    "backup_keep_count": 5,
    # game
    "blood_moon_freq_min": 10,
    "blood_moon_freq_max": 18,
    "blood_essence_yield": 1.0,
    "inventory_stacks": 1.0,
    "build_cost": 1.0,
    "craft_rate": 1.0,
    "recipe_cost": 1.0,
    "research_cost": 1.0,
    "research_time": 1.0,
    "refine_cost": 1.0,
    "refine_rate": 1.0,
    "dismantle": 0.75,
    "repair_cost": 1.0,
    "vamp_hp": 1.0,
    "vamp_phys": 1.0,
    "vamp_spell": 1.0,
    "enemy_hp": 1.0,
    "enemy_power": 1.0,
    "enemy_level": 0,
    "vblood_hp": 1.0,
    "vblood_power": 1.0,
    "vblood_level": 0,
    "trader_stock": 1.0,
    "trader_price": 1.0,
    "trader_restock": 1.0,
}

SERVER_EXE = "VRisingServer.exe"

# ── Color themes ─────────────────────────────────────────────────────────────
THEMES = {
    "Dark Blue (Default)": {
        "DARK_BG":  "#1a1a2e",
        "PANEL_BG": "#16213e",
        "ACCENT":   "#e94560",
        "ACCENT2":  "#0f3460",
        "TEXT":     "#eaeaea",
        "TEXT_DIM": "#8892a4",
        "GREEN":    "#4ecca3",
        "YELLOW":   "#f5a623",
        "ENTRY_BG": "#0d1b2a",
    },
    "Dark Charcoal": {
        "DARK_BG":  "#1c1c1c",
        "PANEL_BG": "#252525",
        "ACCENT":   "#e94560",
        "ACCENT2":  "#3a3a3a",
        "TEXT":     "#e8e8e8",
        "TEXT_DIM": "#888888",
        "GREEN":    "#4ecca3",
        "YELLOW":   "#f5a623",
        "ENTRY_BG": "#111111",
    },
    "Forest Green": {
        "DARK_BG":  "#0d1f0d",
        "PANEL_BG": "#122612",
        "ACCENT":   "#66bb6a",
        "ACCENT2":  "#1b4d1b",
        "TEXT":     "#e8f5e9",
        "TEXT_DIM": "#81c784",
        "GREEN":    "#a5d6a7",
        "YELLOW":   "#ffcc02",
        "ENTRY_BG": "#091409",
    },
    "Midnight Purple": {
        "DARK_BG":  "#1a0a2e",
        "PANEL_BG": "#220d3b",
        "ACCENT":   "#ce93d8",
        "ACCENT2":  "#4a1572",
        "TEXT":     "#f3e5f5",
        "TEXT_DIM": "#ab47bc",
        "GREEN":    "#80cbc4",
        "YELLOW":   "#ffcc02",
        "ENTRY_BG": "#100619",
    },
    "Light / High Contrast": {
        "DARK_BG":  "#e8eaf6",
        "PANEL_BG": "#f5f5f5",
        "ACCENT":   "#c62828",
        "ACCENT2":  "#9fa8da",
        "TEXT":     "#212121",
        "TEXT_DIM": "#616161",
        "GREEN":    "#2e7d32",
        "YELLOW":   "#e65100",
        "ENTRY_BG": "#ffffff",
    },
}


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                saved = json.load(f)
                cfg = DEFAULT_CONFIG.copy()
                cfg.update(saved)
                return cfg
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        messagebox.showerror("Save Error", f"Could not save config:\n{e}")


# ── Profile helpers ──────────────────────────────────────────────────────────

def _profile_path(name):
    """Return the full path for a profile JSON given its display name."""
    safe = re.sub(r'[\\/:*?"<>|]', "_", name).strip()
    return os.path.join(PROFILES_DIR, f"{safe}.json")


def _list_profiles():
    """Return sorted list of profile display names found in PROFILES_DIR."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    names = []
    for fn in os.listdir(PROFILES_DIR):
        if fn.endswith(".json"):
            names.append(fn[:-5])
    return sorted(names)


def _migrate_legacy():
    """Move the old single-config file into a Default profile on first run."""
    if not os.path.exists(LEGACY_CONFIG):
        return
    os.makedirs(PROFILES_DIR, exist_ok=True)
    dest = _profile_path("Default")
    if not os.path.exists(dest):
        shutil.copy2(LEGACY_CONFIG, dest)


def _set_active_profile(name):
    """Point CONFIG_FILE at this profile and remember the choice."""
    global CONFIG_FILE
    CONFIG_FILE = _profile_path(name)
    try:
        with open(_LAST_PROFILE_FILE, "w") as f:
            f.write(name)
    except Exception:
        pass


def _last_profile():
    """Return the name of the last used profile, or None."""
    try:
        with open(_LAST_PROFILE_FILE) as f:
            name = f.read().strip()
            if name and os.path.exists(_profile_path(name)):
                return name
    except Exception:
        pass
    return None


class ProfilePicker(tk.Toplevel):
    """Small dialog shown at startup to pick or create a server profile."""

    def __init__(self, master):
        super().__init__(master)
        self.title("V Rising Server Manager — Select Profile")
        self.resizable(False, False)
        self.configure(bg="#1a1a2e")
        self.chosen = None

        w, h = 420, 320
        self.update_idletasks()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        self._build()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._cancel)

    def _build(self):
        BG    = "#1a1a2e"
        PANEL = "#16213e"
        TEXT  = "#eaeaea"
        DIM   = "#8892a4"
        ACC   = "#e94560"

        tk.Label(self, text="V Rising Server Manager", bg=BG, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(pady=(18, 2))
        tk.Label(self, text="Choose a server profile to manage", bg=BG, fg=DIM,
                 font=("Segoe UI", 9)).pack(pady=(0, 12))

        frame = tk.Frame(self, bg=PANEL, relief="flat", bd=0)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        tk.Label(frame, text="Server profile:", bg=PANEL, fg=TEXT,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=12, pady=(10, 2))

        self._profiles = _list_profiles()
        if not self._profiles:
            self._profiles = ["Default"]

        self._var = tk.StringVar(value=_last_profile() or self._profiles[0])
        self._combo = ttk.Combobox(frame, textvariable=self._var,
                                   values=self._profiles, state="readonly", width=30)
        self._combo.pack(anchor="w", padx=12, pady=(0, 8))

        btn_row = tk.Frame(frame, bg=PANEL)
        btn_row.pack(anchor="w", padx=12, pady=(0, 8))
        tk.Button(btn_row, text="New Profile", command=self._new_profile,
                  bg="#0f3460", fg=TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, pady=3, cursor="hand2").pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="Rename", command=self._rename_profile,
                  bg="#0f3460", fg=TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, pady=3, cursor="hand2").pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="Delete", command=self._delete_profile,
                  bg="#3a1020", fg=TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, pady=3, cursor="hand2").pack(side="left")

        self._info = tk.Label(frame, text="", bg=PANEL, fg=DIM,
                              font=("Segoe UI", 8), wraplength=360, justify="left")
        self._info.pack(anchor="w", padx=12, pady=(0, 6))
        self._update_info()
        self._combo.bind("<<ComboboxSelected>>", lambda _: self._update_info())

        tk.Button(self, text="Open  ▶", command=self._open,
                  bg=ACC, fg="white", relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=20, pady=6,
                  cursor="hand2").pack(pady=(4, 16))

    def _update_info(self):
        name = self._var.get().strip()
        path = _profile_path(name)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                sname = data.get("server_name", "—")
                spath = data.get("server_path", "") or "not set"
                self._info.config(text=f"Server name: {sname}\nInstall path: {spath}")
            except Exception:
                self._info.config(text="(Could not read profile)")
        else:
            self._info.config(text="(New profile — will be created on first save)")

    def _new_profile(self):
        name = self._ask_name("New Profile", "Enter a name for the new profile:")
        if not name:
            return
        if name in self._profiles:
            messagebox.showwarning("Exists", f"A profile named '{name}' already exists.", parent=self)
            return
        self._profiles.append(name)
        self._profiles.sort()
        self._combo["values"] = self._profiles
        self._var.set(name)
        self._update_info()

    def _rename_profile(self):
        old = self._var.get().strip()
        new = self._ask_name("Rename Profile", f"Rename '{old}' to:")
        if not new or new == old:
            return
        old_path = _profile_path(old)
        new_path = _profile_path(new)
        if os.path.exists(old_path):
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not rename: {e}", parent=self)
                return
        self._profiles = [new if p == old else p for p in self._profiles]
        self._profiles.sort()
        self._combo["values"] = self._profiles
        self._var.set(new)
        self._update_info()

    def _delete_profile(self):
        name = self._var.get().strip()
        if not messagebox.askyesno("Delete Profile",
                f"Delete profile '{name}'?\n\nThis removes the saved settings for this server only. The server files themselves are not affected.",
                parent=self):
            return
        path = _profile_path(name)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {e}", parent=self)
                return
        self._profiles = [p for p in self._profiles if p != name]
        if not self._profiles:
            self._profiles = ["Default"]
        self._combo["values"] = self._profiles
        self._var.set(self._profiles[0])
        self._update_info()

    def _ask_name(self, title, prompt):
        dlg = tk.Toplevel(self)
        dlg.title(title)
        dlg.resizable(False, False)
        dlg.configure(bg="#1a1a2e")
        dlg.grab_set()
        w, h = 300, 120
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")
        result = [None]
        tk.Label(dlg, text=prompt, bg="#1a1a2e", fg="#eaeaea",
                 font=("Segoe UI", 9)).pack(pady=(14, 4), padx=14)
        var = tk.StringVar()
        entry = tk.Entry(dlg, textvariable=var, font=("Segoe UI", 10), width=26)
        entry.pack(padx=14)
        entry.focus_set()
        def _ok(e=None):
            result[0] = var.get().strip()
            dlg.destroy()
        def _cancel(e=None):
            dlg.destroy()
        entry.bind("<Return>", _ok)
        entry.bind("<Escape>", _cancel)
        tk.Button(dlg, text="OK", command=_ok, bg="#e94560", fg="white",
                  relief="flat", font=("Segoe UI", 9), padx=12, pady=3).pack(pady=8)
        dlg.wait_window()
        return result[0]

    def _open(self):
        name = self._var.get().strip()
        if not name:
            return
        self.chosen = name
        self.destroy()

    def _cancel(self):
        self.destroy()


class VRisingManager(tk.Tk):
    def __init__(self, profile_name="Default"):
        super().__init__()
        self.profile_name = profile_name
        self.title(f"V Rising Server Manager — {profile_name}")
        self.resizable(True, True)
        self.minsize(800, 700)
        # Start at a reasonable default — small enough to run multiple side by side
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = min(1000, sw - 40), min(780, sh - 60)
        x = (sw - w) // 2
        y = max(0, (sh - h) // 2)
        self.geometry(f"{w}x{h}+{x}+{y}")
        self.configure(bg="#1a1a2e")

        self.cfg = load_config()
        self.server_process = None
        self.monitor_thread = None
        self._running = True
        self._restart_cancel = False

        self._setup_styles()
        self._build_ui()
        self._load_ui_from_config()
        self._import_from_server_files()   # overlay values from actual server JSONs if present
        self._start_monitor()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _update_title(self):
        path = ""
        try:
            path = self.path_var.get().strip()
        except AttributeError:
            pass   # path_var not created yet
        if path:
            self.title(f"V Rising Server Manager — {self.profile_name}  [{path}]")
        else:
            self.title(f"V Rising Server Manager — {self.profile_name}")
        # Update header bar path label
        try:
            self._header_path_lbl.config(text=path if path else "")
        except AttributeError:
            pass   # header label not built yet

    # ── Styles ──────────────────────────────────────────────────────────────
    def _setup_styles(self):
        theme_name = self.cfg.get("theme", "Dark Blue (Default)")
        t = THEMES.get(theme_name, THEMES["Dark Blue (Default)"])
        self.DARK_BG    = t["DARK_BG"]
        self.PANEL_BG   = t["PANEL_BG"]
        self.ACCENT     = t["ACCENT"]
        self.ACCENT2    = t["ACCENT2"]
        self.TEXT       = t["TEXT"]
        self.TEXT_DIM   = t["TEXT_DIM"]
        self.GREEN      = t["GREEN"]
        self.YELLOW     = t["YELLOW"]
        self.ENTRY_BG   = t["ENTRY_BG"]
        self.SLIDER_TRG = self.ACCENT

        self._apply_ttk_styles()

    def _apply_ttk_styles(self):
        """Configure (or reconfigure) all ttk styles from current color vars."""
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook",          background=self.DARK_BG,  borderwidth=0)
        style.configure("TNotebook.Tab",      background=self.ACCENT2,  foreground=self.TEXT,
                         padding=[14, 6],     font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", self.ACCENT)],
                  foreground=[("selected", "#ffffff")])
        style.configure("TFrame",             background=self.PANEL_BG)
        style.configure("TLabel",             background=self.PANEL_BG, foreground=self.TEXT,
                         font=("Segoe UI", 9))
        style.configure("TCheckbutton",       background=self.PANEL_BG, foreground=self.TEXT,
                         font=("Segoe UI", 9))
        style.map("TCheckbutton",             background=[("active", self.PANEL_BG)])
        style.configure("TScale",             background=self.PANEL_BG, troughcolor=self.ACCENT2,
                         sliderlength=18,     sliderrelief="flat")
        style.configure("TEntry",             fieldbackground=self.ENTRY_BG, foreground=self.TEXT,
                         insertcolor=self.TEXT, borderwidth=1, relief="flat")
        style.configure("TSpinbox",           fieldbackground=self.ENTRY_BG, foreground=self.TEXT,
                         insertcolor=self.TEXT, arrowcolor=self.TEXT)
        style.configure("TCombobox",          fieldbackground=self.ENTRY_BG, foreground=self.TEXT,
                         selectbackground=self.ACCENT2)
        style.map("TCombobox",                fieldbackground=[("readonly", self.ENTRY_BG)])

    # ── Main UI layout ───────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        header = tk.Frame(self, bg=self.ACCENT2, pady=10)
        header.pack(fill="x")
        tk.Label(header, text="⚔  V Rising Server Manager",
                 bg=self.ACCENT2, fg=self.TEXT, font=("Segoe UI", 14, "bold")).pack(side="left", padx=16)

        # Path label — centre of header, updates when path changes
        self._header_path_lbl = tk.Label(header, text="",
                                          bg=self.ACCENT2, fg=self.TEXT,
                                          font=("Segoe UI", 11))
        self._header_path_lbl.pack(side="left", padx=(12, 0))

        # Profile indicator + switch button (right side of header)
        tk.Button(header, text=f"Switch Profile",
                  command=self._switch_profile,
                  bg=self.DARK_BG, fg=self.TEXT_DIM, relief="flat",
                  font=("Segoe UI", 8), padx=8, pady=2,
                  cursor="hand2").pack(side="right", padx=(4, 16))
        self._profile_lbl = tk.Label(header, text=f"Profile: {self.profile_name}",
                                      bg=self.ACCENT2, fg=self.TEXT_DIM,
                                      font=("Segoe UI", 8))
        self._profile_lbl.pack(side="right", padx=(0, 4))

        # ── Status bar ──
        status_bar = tk.Frame(self, bg=self.ENTRY_BG, pady=6)
        status_bar.pack(fill="x")

        self.status_dot = tk.Label(status_bar, text="●", font=("Segoe UI", 14),
                                   bg=self.ENTRY_BG, fg="#555")
        self.status_dot.pack(side="left", padx=(14, 4))

        self.status_label = tk.Label(status_bar, text="Server: Stopped",
                                     bg=self.ENTRY_BG, fg=self.TEXT_DIM,
                                     font=("Segoe UI", 9, "bold"))
        self.status_label.pack(side="left")

        self.cpu_label = tk.Label(status_bar, text="", bg=self.ENTRY_BG,
                                  fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.cpu_label.pack(side="right", padx=14)

        # One-time restart countdown — shown when a restart is scheduled/running
        self.restart_countdown_lbl = tk.Label(status_bar, text="", bg=self.ENTRY_BG,
                                              fg=self.YELLOW, font=("Segoe UI", 8, "bold"))
        self.restart_countdown_lbl.pack(side="left", padx=(16, 0))

        # Daily restart indicator — shown whenever daily restart is enabled
        self.daily_restart_status_lbl = tk.Label(status_bar, text="", bg=self.ENTRY_BG,
                                                  fg=self.TEXT, font=("Segoe UI", 8, "bold"))
        self.daily_restart_status_lbl.pack(side="left", padx=(16, 0))

        # ── Control buttons ──
        btn_frame = tk.Frame(self, bg=self.DARK_BG, pady=8)
        btn_frame.pack(fill="x", padx=14)

        self.start_btn = tk.Button(btn_frame, text="▶  Start Server",
                                   command=self._start_server,
                                   bg=self.GREEN, fg="#0d1b2a",
                                   font=("Segoe UI", 10, "bold"),
                                   relief="flat", padx=16, pady=6, cursor="hand2")
        self.start_btn.pack(side="left", padx=(0, 8))

        self.stop_btn = tk.Button(btn_frame, text="■  Stop Server",
                                  command=self._stop_server,
                                  bg=self.ACCENT, fg="white",
                                  font=("Segoe UI", 10, "bold"),
                                  relief="flat", padx=16, pady=6,
                                  state="disabled", cursor="hand2")
        self.stop_btn.pack(side="left", padx=(0, 8))

        self.save_btn = tk.Button(btn_frame, text="💾  Save Settings",
                                  command=self._save_settings,
                                  bg=self.ACCENT2, fg=self.TEXT,
                                  font=("Segoe UI", 10, "bold"),
                                  relief="flat", padx=16, pady=6, cursor="hand2")
        self.save_btn.pack(side="right")

        # ── Notebook tabs ──
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=(4, 10))

        self._build_tab_setup()
        self._build_tab_server()
        self._build_tab_game()
        self._build_tab_player()
        self._build_tab_network()
        self._build_tab_admin()
        self._build_tab_tools()
        self._build_tab_log()

        # Auto-focus the canvas of whichever scrollable tab is selected so
        # the mousewheel works immediately without needing to click first
        def _focus_active_tab_canvas(event=None):
            try:
                selected = self.notebook.select()
                tab_frame = self.nametowidget(selected)
                # Walk children looking for a Canvas
                for child in tab_frame.winfo_children():
                    if isinstance(child, tk.Canvas):
                        child.focus_set()
                        return
            except Exception:
                pass
        self.notebook.bind("<<NotebookTabChanged>>", _focus_active_tab_canvas)

    # ── Helper: scrollable tab frame ────────────────────────────────────────
    def _scrollable_tab(self, label):
        outer = ttk.Frame(self.notebook)
        canvas = tk.Canvas(outer, bg=self.PANEL_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _scroll_wheel(e):
            canvas.yview_scroll(int(-1*(e.delta/120)), "units")

        def _scroll_up(e):
            canvas.yview_scroll(-1, "units")

        def _scroll_down(e):
            canvas.yview_scroll(1, "units")

        # Bind mousewheel on both canvas and inner so scroll works without
        # needing to click first — also propagate from any child widget
        for widget in (canvas, inner):
            widget.bind("<MouseWheel>", _scroll_wheel)   # Windows
            widget.bind("<Button-4>",   _scroll_up)      # Linux scroll up
            widget.bind("<Button-5>",   _scroll_down)    # Linux scroll down

        # Keyboard scrolling — works when Chrome Remote Desktop scroll doesn't
        canvas.bind("<Prior>",    lambda e: canvas.yview_scroll(-5, "units"))  # Page Up
        canvas.bind("<Next>",     lambda e: canvas.yview_scroll(5,  "units"))  # Page Down
        canvas.bind("<Up>",       lambda e: canvas.yview_scroll(-1, "units"))
        canvas.bind("<Down>",     lambda e: canvas.yview_scroll(1,  "units"))
        canvas.bind("<Home>",     lambda e: canvas.yview_moveto(0))
        canvas.bind("<End>",      lambda e: canvas.yview_moveto(1))
        # Focus canvas on click so keyboard events work
        canvas.bind("<Button-1>", lambda e: canvas.focus_set())
        inner.bind("<Button-1>",  lambda e: canvas.focus_set())

        # Auto-focus canvas when this tab is raised so scroll works immediately
        outer.bind("<Visibility>", lambda e: canvas.focus_set())
        self.notebook.add(outer, text=label)
        return inner

    # ── Helper: slider row ───────────────────────────────────────────────────
    def _slider_row(self, parent, row, label, var, from_, to, resolution=0.01,
                    fmt="{:.2f}", unit="", tooltip=""):
        ttk.Label(parent, text=label, width=28, anchor="w").grid(
            row=row, column=0, sticky="w", padx=(10, 4), pady=5)
        sl = ttk.Scale(parent, from_=from_, to=to, variable=var,
                       orient="horizontal", length=240)
        sl.grid(row=row, column=1, sticky="ew", padx=4)
        val_lbl = tk.Label(parent, text=fmt.format(var.get()) + unit,
                           bg=self.PANEL_BG, fg=self.ACCENT, width=8,
                           font=("Consolas", 9, "bold"), anchor="w")
        val_lbl.grid(row=row, column=2, sticky="w", padx=(4, 10))
        # Update label whenever the variable changes — dragging OR programmatic set
        def _on_var_change(*_, v=var, f=fmt, u=unit, lbl=val_lbl):
            try:
                lbl.config(text=f.format(float(v.get())) + u)
            except Exception:
                pass
        var.trace_add("write", _on_var_change)
        if tooltip:
            tip_lbl = tk.Label(parent, text="ℹ", bg=self.PANEL_BG,
                               fg=self.TEXT_DIM, font=("Segoe UI", 9),
                               cursor="question_arrow")
            tip_lbl.grid(row=row, column=3, sticky="w", padx=(0, 6))
            self._bind_tooltip(tip_lbl, tooltip)
        return sl

    def _bind_tooltip(self, widget, text):
        """Show a floating tooltip popup on hover."""
        tip_win = None

        def show(event):
            nonlocal tip_win
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            tip_win = tk.Toplevel(widget)
            tip_win.wm_overrideredirect(True)
            tip_win.wm_geometry(f"+{x}+{y}")
            tip_win.attributes("-topmost", True)
            lbl = tk.Label(tip_win, text=text, justify="left",
                           bg="#1a1a2e", fg="#eaeaea",
                           font=("Segoe UI", 8),
                           relief="solid", borderwidth=1,
                           wraplength=300, padx=6, pady=4)
            lbl.pack()

        def hide(event):
            nonlocal tip_win
            if tip_win:
                tip_win.destroy()
                tip_win = None

        widget.bind("<Enter>", show)
        widget.bind("<Leave>", hide)

    def _password_entry(self, parent, var, width=24):
        """Create a password entry with a show/hide toggle button. Returns the frame."""
        frame = tk.Frame(parent, bg=self.PANEL_BG)
        entry = ttk.Entry(frame, textvariable=var, show="*", width=width)
        entry.pack(side="left")
        showing = tk.BooleanVar(value=False)

        def toggle():
            if showing.get():
                entry.config(show="*")
                showing.set(False)
                btn.config(text="👁")
            else:
                entry.config(show="")
                showing.set(True)
                btn.config(text="🙈")

        btn = tk.Button(frame, text="👁", command=toggle,
                        bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                        font=("Segoe UI", 9), padx=4, pady=1,
                        cursor="hand2", width=2)
        btn.pack(side="left", padx=(3,0))
        self._bind_tooltip(btn, "Click to show/hide password")
        return frame

    # ── Helper: section header ───────────────────────────────────────────────
    def _section(self, parent, row, text):
        f = tk.Frame(parent, bg=self.ACCENT2, height=1)
        f.grid(row=row, column=0, columnspan=4, sticky="ew", padx=10, pady=(12, 2))
        ttk.Label(parent, text=text, font=("Segoe UI", 9, "bold"),
                  foreground=self.ACCENT).grid(
            row=row+1, column=0, columnspan=4, sticky="w", padx=12, pady=(0, 4))

    # ── Tab: Setup / Install ─────────────────────────────────────────────────
    def _build_tab_setup(self):
        outer = ttk.Frame(self.notebook)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(6, weight=1)
        self.notebook.add(outer, text="  Setup  ")

        # ── Intro ──
        intro = tk.Label(outer,
            text="First time setup — follow the steps below in order to download and install "
                 "the V Rising dedicated server. You only need to do this once per server.\n"
                 "No Steam account login is required — the download is anonymous.\n"
                 "Tip: give each server its own folder (e.g. VRisingServer_PvE, VRisingServer_PvP) "
                 "so you can switch between them easily. SteamCMD only needs one folder regardless of how many servers you have.",
            bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 8),
            wraplength=680, justify="left")
        intro.grid(row=0, column=0, sticky="ew", padx=14, pady=(10,4))

        # ── Step 1: Install folder ──
        self._section_plain(outer, 1, "Step 1 — Choose where to install the server")
        s1 = tk.Frame(outer, bg=self.PANEL_BG)
        s1.grid(row=2, column=0, sticky="ew", padx=10, pady=(2,4))
        s1.columnconfigure(1, weight=1)

        tk.Label(s1, text="Server install folder:", bg=self.PANEL_BG, fg=self.TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0,6))
        self.setup_install_var = tk.StringVar(value="C:\\gameservers\\VRisingServer")
        ttk.Entry(s1, textvariable=self.setup_install_var, width=44).grid(
            row=0, column=1, sticky="ew", padx=4)
        tk.Button(s1, text="Browse…", command=self._setup_browse_install,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, cursor="hand2").grid(row=0, column=2, padx=4)

        tk.Label(s1,
            text="Give each server its own folder — e.g. VRisingServer_PvE, VRisingServer_PvP, etc.\n"
                 "This is where VRisingServer.exe will be installed. The folder will be created if it doesn't exist.",
            bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 7)).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2,0))

        # ── Step 2: SteamCMD ──
        self._section_plain(outer, 3, "Step 2 — Download SteamCMD  (the server download tool — only needed once)")
        s2 = tk.Frame(outer, bg=self.PANEL_BG)
        s2.grid(row=4, column=0, sticky="ew", padx=10, pady=(2,4))
        s2.columnconfigure(1, weight=1)

        tk.Label(s2, text="SteamCMD folder:", bg=self.PANEL_BG, fg=self.TEXT,
                 font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", padx=(0,6))
        self.setup_steamcmd_var = tk.StringVar(value=self.cfg.get("steamcmd_path", "C:\\gameservers\\steamcmd"))
        self.setup_steamcmd_var.trace_add("write", lambda *_: self._save_steamcmd_path())
        ttk.Entry(s2, textvariable=self.setup_steamcmd_var, width=32).grid(
            row=0, column=1, sticky="ew", padx=4)
        tk.Button(s2, text="Browse…", command=self._setup_browse_steamcmd,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, cursor="hand2").grid(row=0, column=2, padx=4)

        tk.Label(s2,
            text="Keep SteamCMD in its own separate folder — you only ever need one copy of it no matter how many servers you run.",
            bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 7)).grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(2,4))

        self.setup_steamcmd_btn = tk.Button(s2, text="⬇  Download SteamCMD",
                  command=self._setup_download_steamcmd,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2")
        self.setup_steamcmd_btn.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6,0))

        self.setup_steamcmd_status = tk.Label(s2, text="", bg=self.PANEL_BG,
                                               fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.setup_steamcmd_status.grid(row=2, column=0, columnspan=3, sticky="w", pady=(2,0))

        # ── Step 3: Install server ──
        self._section_plain(outer, 5, "Step 3 — Download & Install V Rising Dedicated Server")
        s3 = tk.Frame(outer, bg=self.PANEL_BG)
        s3.grid(row=6, column=0, sticky="nsew", padx=10, pady=(2,4))
        s3.columnconfigure(0, weight=1)
        s3.rowconfigure(1, weight=1)

        btn_row = tk.Frame(s3, bg=self.PANEL_BG)
        btn_row.grid(row=0, column=0, sticky="ew", pady=(0,4))

        self.setup_install_btn = tk.Button(btn_row,
                  text="⬇  Install / Update V Rising Server",
                  command=self._setup_install_server,
                  bg=self.GREEN, fg="#0d1b2a", relief="flat",
                  font=("Segoe UI", 10, "bold"), padx=16, pady=6, cursor="hand2")
        self.setup_install_btn.pack(side="left", padx=(0,10))
        self.setup_use_btn = tk.Button(btn_row,
                  text="✓  Use this install path",
                  command=self._setup_apply_path,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=6, cursor="hand2",
                  state="disabled")
        self.setup_use_btn.pack(side="left")

        tk.Label(btn_row,
            text="  ← click after install finishes to set this as your server path",
            bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 7)).pack(side="left")

        # Output console
        out_frame = tk.Frame(s3, bg="#0a1020")
        out_frame.grid(row=1, column=0, sticky="nsew")
        out_frame.columnconfigure(0, weight=1)
        out_frame.rowconfigure(0, weight=1)

        self.setup_output = tk.Text(out_frame, bg="#0a1020", fg=self.GREEN,
                                     font=("Consolas", 8), relief="flat",
                                     state="disabled", wrap="none", height=12)
        self.setup_output.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(out_frame, orient="vertical", command=self.setup_output.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(out_frame, orient="horizontal", command=self.setup_output.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.setup_output.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._setup_log("Welcome! Follow Steps 1-3 above to install your V Rising server.\n"
                        "If you already have the server installed, skip to the Server tab and set your path there.\n\n"
                        "Already been playing? Use the 'Find Existing World' section on the Tools tab\n"
                        "to locate and back up your existing save before changing any settings.\n")

        # ── Already have a world? ──
        self._section_plain(outer, 7, "Already been playing?  — Find & protect your existing world save")
        existing_frame = tk.Frame(outer, bg=self.PANEL_BG)
        existing_frame.grid(row=8, column=0, sticky="ew", padx=10, pady=(2,8))
        existing_frame.columnconfigure(1, weight=1)

        tk.Label(existing_frame,
            text="If you have an existing world you don't want to lose, click the button below.\n"
                 "The manager will scan both your server folder AND your local game client saves\n"
                 "so you can find and protect your world before making any changes.",
            bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 8),
            justify="left").grid(row=0, column=0, columnspan=3, sticky="w", padx=4, pady=(0,6))

        btn_row2 = tk.Frame(existing_frame, bg=self.PANEL_BG)
        btn_row2.grid(row=1, column=0, columnspan=3, sticky="w", padx=4)

        tk.Button(btn_row2, text="🔍  Find Existing World Saves",
                  command=self._setup_find_saves,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(
            side="left", padx=(0,8))

        tk.Button(btn_row2, text="📋  Copy Local Save to Server",
                  command=self._setup_copy_local_to_server,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left")

        self.setup_saves_status = tk.Label(existing_frame, text="", bg=self.PANEL_BG,
                                            fg=self.TEXT_DIM, font=("Segoe UI", 8),
                                            justify="left", wraplength=700)
        self.setup_saves_status.grid(row=2, column=0, columnspan=3, sticky="w",
                                      padx=4, pady=(6,0))

    # ── Setup helper methods ─────────────────────────────────────────────────
    def _setup_log(self, text, color=None):
        self.setup_output.configure(state="normal")
        self.setup_output.insert(tk.END, text)
        self.setup_output.see(tk.END)
        self.setup_output.configure(state="disabled")

    def _setup_find_saves(self):
        """Scan both the server folder and local game client saves."""
        base = os.path.normpath(self.setup_install_var.get().strip())

        found_saves = []

        def scan_dir(saves_root, label):
            if not os.path.isdir(saves_root):
                return
            for root, dirs, files in os.walk(saves_root):
                depth = root.replace(saves_root, "").count(os.sep)
                if depth > 3:
                    continue
                save_files = [f for f in files if f.endswith((".save", ".save.gz", ".zip"))]
                if save_files:
                    size = sum(
                        os.path.getsize(os.path.join(root, f))
                        for f in save_files
                    ) / (1024 * 1024)
                    mtime = max(
                        os.path.getmtime(os.path.join(root, f))
                        for f in save_files
                    )
                    last_played = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    found_saves.append((label, root, len(save_files), size, last_played))

        # Server saves
        if base and os.path.isdir(base):
            scan_dir(os.path.join(base, "save-data", "Saves"), "Server")
            scan_dir(os.path.join(base, "save-data", "v3"),    "Server")

        # Local game client saves — where the game itself stores worlds
        local_v3 = os.path.expandvars(
            r"%APPDATA%\..\LocalLow\Stunlock Studios\VRising\Saves\v3")
        local_v1 = os.path.expandvars(
            r"%APPDATA%\..\LocalLow\Stunlock Studios\VRising\Saves\v1")
        local_cloud = os.path.expandvars(
            r"%APPDATA%\..\LocalLow\Stunlock Studios\VRising\CloudSaves")
        scan_dir(local_v3,    "Local game client (v3)")
        scan_dir(local_v1,    "Local game client (v1)")
        scan_dir(local_cloud, "Steam Cloud save")

        if found_saves:
            lines = ["Found the following world saves:\n"]
            for label, path, count, size, last in found_saves:
                lines.append(f"  📁 [{label}]")
                lines.append(f"     {path}")
                lines.append(f"     {count} save file(s)  •  {size:.1f} MB  •  Last played: {last}\n")
            lines.append("─" * 60)
            lines.append("If you see 'Local game client' saves above and want to move")
            lines.append("that world to your dedicated server, click")
            lines.append("'📋 Copy Local Save to Server' and follow the steps.")
            self.setup_saves_status.config(text="\n".join(lines), fg=self.GREEN)
        else:
            self.setup_saves_status.config(
                text="No save files found in server folder or local game client location.\n\n"
                     "Local game client saves should be at:\n"
                     r"  %APPDATA%\..\LocalLow\Stunlock Studios\VRising\Saves\v3" + "\n\n"
                     "Note: AppData is a hidden folder. In File Explorer, click View > Show > Hidden Items.",
                fg=self.TEXT_DIM)

    def _setup_copy_local_to_server(self):
        """Walk user through copying a local game save to the dedicated server."""
        server_base = os.path.normpath(self.setup_install_var.get().strip())
        if not server_base or not os.path.isdir(server_base):
            messagebox.showerror("No Server Path",
                "Set your server folder path in Step 1 first.")
            return

        # Find local save worlds to pick from
        local_v3 = os.path.expandvars(
            r"%APPDATA%\..\LocalLow\Stunlock Studios\VRising\Saves\v3")
        local_v1 = os.path.expandvars(
            r"%APPDATA%\..\LocalLow\Stunlock Studios\VRising\Saves\v1")

        worlds = []
        for saves_root in [local_v3, local_v1]:
            if not os.path.isdir(saves_root):
                continue
            for world_folder in os.listdir(saves_root):
                world_path = os.path.join(saves_root, world_folder)
                if not os.path.isdir(world_path):
                    continue
                save_files = [f for f in os.listdir(world_path)
                              if f.endswith((".save", ".save.gz"))]
                if save_files:
                    mtime = max(
                        os.path.getmtime(os.path.join(world_path, f))
                        for f in save_files)
                    last = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                    worlds.append((world_folder, world_path, last))

        if not worlds:
            messagebox.showinfo("No Local Saves Found",
                "No local game client saves were found at:\n"
                f"{local_v3}\n\n"
                "Make sure you have run V Rising locally at least once,\n"
                "or check that AppData is not hidden in File Explorer\n"
                "(View > Show > Hidden Items).")
            return

        # Let user pick which world to copy
        pick_win = tk.Toplevel(self)
        pick_win.title("Copy Local Save to Server")
        pick_win.configure(bg=self.DARK_BG)
        pick_win.geometry("560x320")
        pick_win.attributes("-topmost", True)

        tk.Label(pick_win,
            text="Select the local world you want to copy to the dedicated server:",
            bg=self.DARK_BG, fg=self.TEXT, font=("Segoe UI", 9)).pack(
            padx=14, pady=(12,4), anchor="w")

        listbox = tk.Listbox(pick_win, bg="#0d1b2a", fg=self.TEXT,
                             selectbackground=self.ACCENT, font=("Consolas", 9),
                             relief="flat", height=6)
        listbox.pack(fill="both", expand=True, padx=14, pady=4)
        for name, path, last in worlds:
            listbox.insert(tk.END, f"{name}   (last played: {last})")
        listbox.selection_set(0)

        tk.Label(pick_win,
            text="⚠  The server must be STOPPED before copying. Make sure it is not running.",
            bg=self.DARK_BG, fg=self.YELLOW, font=("Segoe UI", 8)).pack(
            padx=14, pady=(0,4), anchor="w")

        def do_copy():
            idx = listbox.curselection()
            if not idx:
                return
            world_name, src_path, _ = worlds[idx[0]]

            # Destination: server save-data/Saves/v3/<world_name>
            dest_saves = os.path.join(server_base, "save-data", "Saves", "v3")
            dest_path  = os.path.join(dest_saves, world_name)

            if os.path.exists(dest_path):
                if not messagebox.askyesno("Already Exists",
                    f"A save named '{world_name}' already exists on the server.\n\n"
                    "Overwrite it?", parent=pick_win):
                    return

            try:
                os.makedirs(dest_saves, exist_ok=True)
                if os.path.exists(dest_path):
                    shutil.rmtree(dest_path)
                shutil.copytree(src_path, dest_path)

                # Update SaveName in config
                self.save_name_var.set(world_name)
                self.cfg["save_name"] = world_name

                pick_win.destroy()
                messagebox.showinfo("Copy Complete",
                    f"World '{world_name}' copied to:\n{dest_path}\n\n"
                    f"The Save Name on the Server tab has been set to '{world_name}'.\n\n"
                    "Click Save Settings on the Server tab to write this to\n"
                    "ServerHostSettings.json before starting the server.")
            except Exception as e:
                messagebox.showerror("Copy Failed", f"Could not copy save:\n{e}",
                                     parent=pick_win)

        btn_row = tk.Frame(pick_win, bg=self.DARK_BG)
        btn_row.pack(fill="x", padx=14, pady=(0,12))
        tk.Button(btn_row, text="📋  Copy to Server", command=do_copy,
                  bg=self.GREEN, fg="#0d1b2a", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4,
                  cursor="hand2").pack(side="left", padx=(0,8))
        tk.Button(btn_row, text="Cancel", command=pick_win.destroy,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9), padx=8, pady=4,
                  cursor="hand2").pack(side="left")

    def _setup_browse_install(self):
        folder = filedialog.askdirectory(title="Choose server install folder")
        if folder:
            self.setup_install_var.set(os.path.normpath(folder))

    def _setup_browse_steamcmd(self):
        folder = filedialog.askdirectory(title="Choose SteamCMD folder")
        if folder:
            self.setup_steamcmd_var.set(os.path.normpath(folder))

    def _save_steamcmd_path(self):
        try:
            self.cfg["steamcmd_path"] = self.setup_steamcmd_var.get().strip()
            save_config(self.cfg)
        except Exception:
            pass

    def _setup_download_steamcmd(self):
        """Download and extract SteamCMD to the chosen folder."""
        dest = os.path.normpath(self.setup_steamcmd_var.get().strip())
        steamcmd_exe = os.path.join(dest, "steamcmd.exe")

        existing = self._find_steamcmd_exe()
        if existing:
            self.setup_steamcmd_status.config(
                text=f"✓ SteamCMD already exists at {existing}", fg=self.GREEN)
            return

        self.setup_steamcmd_btn.config(state="disabled")
        self.setup_steamcmd_status.config(text="Downloading...", fg=self.YELLOW)
        self._setup_log(f"\nDownloading SteamCMD to {dest}...\n")

        def do_download():
            import urllib.request, zipfile, io
            try:
                os.makedirs(dest, exist_ok=True)
                url = "https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip"
                self.after(0, lambda: self._setup_log("  Connecting to Steam CDN...\n"))
                with urllib.request.urlopen(url, timeout=30) as resp:
                    data = resp.read()
                self.after(0, lambda: self._setup_log(f"  Downloaded {len(data)//1024} KB — extracting...\n"))
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    z.extractall(dest)
                self.after(0, lambda: self._setup_log(f"  ✓ SteamCMD extracted to {dest}\n"))
                self.after(0, lambda: self.setup_steamcmd_status.config(
                    text=f"✓ SteamCMD ready at {steamcmd_exe}", fg=self.GREEN))
            except Exception as e:
                self.after(0, lambda err=e: self._setup_log(f"  ✗ Download failed: {err}\n"))
                self.after(0, lambda err=e: self.setup_steamcmd_status.config(
                    text=f"✗ Failed: {err}", fg=self.ACCENT))
            finally:
                self.after(0, lambda: self.setup_steamcmd_btn.config(state="normal"))

        threading.Thread(target=do_download, daemon=True).start()

    def _find_steamcmd_exe(self):
        """Find steamcmd.exe — checks the configured folder and its bin subfolder."""
        steamcmd_dir = os.path.normpath(self.setup_steamcmd_var.get().strip())
        for candidate in [
            os.path.join(steamcmd_dir, "steamcmd.exe"),
            os.path.join(steamcmd_dir, "bin", "steamcmd.exe"),
        ]:
            if os.path.isfile(candidate):
                return candidate
        return None

    def _setup_install_server(self):
        """Run SteamCMD to download/update the V Rising dedicated server."""
        steamcmd_exe = self._find_steamcmd_exe()
        install_dir  = os.path.normpath(self.setup_install_var.get().strip())

        if not steamcmd_exe:
            steamcmd_dir = os.path.normpath(self.setup_steamcmd_var.get().strip())
            messagebox.showerror("SteamCMD Not Found",
                f"steamcmd.exe not found in:\n{steamcmd_dir}\n  or\n{os.path.join(steamcmd_dir, 'bin')}"
                "\n\nComplete Step 2 first.")
            return

        # Warn if server appears to be running
        if self.server_process or self._find_server_process():
            if not messagebox.askyesno("Server Is Running",
                "The server appears to be running.\n\n"
                "You must stop it before updating — SteamCMD cannot\n"
                "update files that are currently in use.\n\n"
                "Stop the server now and continue?"):
                return
            self._stop_server()
            time.sleep(2)  # Give it a moment to fully close

        os.makedirs(install_dir, exist_ok=True)
        self.setup_install_btn.config(state="disabled")
        self.setup_use_btn.config(state="disabled")
        self._setup_log(f"\n{'='*60}\n")
        self._setup_log(f"Installing V Rising Dedicated Server to:\n  {install_dir}\n\n")
        self._setup_log("This may take several minutes on first install.\n")
        self._setup_log("Updates are much faster — only changed files are downloaded.\n\n")

        # V Rising dedicated server Steam App ID: 1829350
        cmd = [
            steamcmd_exe,
            "+force_install_dir", install_dir,
            "+login", "anonymous",
            "+app_update", "1829350", "validate",
            "+quit"
        ]

        def run_steamcmd():
            """Run SteamCMD and return the exit code, streaming output to the log."""
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            # Stream output line by line; SteamCMD can be quiet for long stretches
            # so we also show a periodic "still running" heartbeat
            last_output = [time.time()]
            def heartbeat():
                if proc.poll() is None:
                    elapsed = int(time.time() - last_output[0])
                    if elapsed >= 15:
                        self.after(0, lambda: self._setup_log(
                            f"  (still running — {elapsed}s since last output, please wait...)\n"))
                    self.after(5000, heartbeat)
            self.after(5000, heartbeat)
            for line in proc.stdout:
                last_output[0] = time.time()
                self.after(0, lambda l=line.rstrip(): self._setup_log(l + "\n"))
            proc.wait()
            return proc.returncode

        def do_install():
            try:
                rc = run_steamcmd()

                # Exit code 8 means SteamCMD updated itself — just run it again
                if rc == 8:
                    self.after(0, lambda: self._setup_log(
                        "\n⟳ SteamCMD updated itself — restarting download automatically...\n\n"))
                    rc = run_steamcmd()

                if rc == 0:
                    exe = os.path.join(install_dir, SERVER_EXE)
                    if os.path.isfile(exe):
                        self.after(0, lambda: self._setup_log(
                            f"\n✓ Install complete! VRisingServer.exe found at:\n  {install_dir}\n\n"
                            "Click '✓ Use this install path' to set it on the Server tab.\n"))
                        self.after(0, lambda: self.setup_use_btn.config(state="normal"))
                    else:
                        self.after(0, lambda: self._setup_log(
                            "\n⚠ SteamCMD finished but VRisingServer.exe was not found.\n"
                            "Check the output above for errors.\n"))
                else:
                    self.after(0, lambda c=rc: self._setup_log(
                        f"\n✗ SteamCMD exited with code {c}. Check the output above for errors.\n"))
            except Exception as e:
                self.after(0, lambda err=e: self._setup_log(f"\n✗ Error: {err}\n"))
            finally:
                self.after(0, lambda: self.setup_install_btn.config(state="normal"))

        threading.Thread(target=do_install, daemon=True).start()

    def _setup_apply_path(self):
        """Copy the install path to the Server tab path field."""
        install_dir = os.path.normpath(self.setup_install_var.get().strip())
        self.path_var.set(install_dir)
        self.cfg["server_path"] = install_dir
        save_config(self.cfg)
        messagebox.showinfo("Path Set",
            f"Server path set to:\n{install_dir}\n\n"
            "Go to the Server tab to configure your settings, then click Start Server.")
        # Switch to server tab
        self.notebook.select(1)

    # ── Tab: Server Path ────────────────────────────────────────────────────
    def _build_tab_server(self):
        tab = self._scrollable_tab("  Server  ")
        tab.columnconfigure(1, weight=1)

        self._section(tab, 0, "Server Executable")

        ttk.Label(tab, text="Server Folder Path:").grid(
            row=2, column=0, sticky="w", padx=(10, 4), pady=6)
        self.path_var = tk.StringVar()
        self.path_var.trace_add("write", lambda *_: self._update_title())
        path_entry = ttk.Entry(tab, textvariable=self.path_var, width=44)
        path_entry.grid(row=2, column=1, sticky="ew", padx=4, pady=6)
        tk.Button(tab, text="Browse…", command=self._browse_path,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, cursor="hand2").grid(
            row=2, column=2, padx=4)

        ttk.Label(tab, text=f"(Folder containing {SERVER_EXE})",
                  foreground=self.TEXT_DIM, font=("Segoe UI", 7)).grid(
            row=3, column=1, sticky="w", padx=4)

        tk.Button(tab, text="↺  Reload from Server Files",
                  command=self._reload_from_server,
                  bg="#0d2b0d", fg=self.GREEN, relief="flat",
                  font=("Segoe UI", 8, "bold"), padx=10, pady=3, cursor="hand2").grid(
            row=3, column=2, padx=4, pady=2, sticky="w")

        self._section(tab, 4, "Server Identity")

        ttk.Label(tab, text="Server Name:").grid(row=6, column=0, sticky="w", padx=(10,4), pady=5)
        self.server_name_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.server_name_var, width=32).grid(
            row=6, column=1, sticky="ew", padx=4)

        ttk.Label(tab, text="Description:").grid(row=7, column=0, sticky="w", padx=(10,4), pady=5)
        self.description_var = tk.StringVar()
        ttk.Entry(tab, textvariable=self.description_var, width=32).grid(
            row=7, column=1, sticky="ew", padx=4)

        ttk.Label(tab, text="Password (blank = public):").grid(row=8, column=0, sticky="w", padx=(10,4), pady=5)
        self.password_var = tk.StringVar()
        self._password_entry(tab, self.password_var, width=24).grid(
            row=8, column=1, sticky="w", padx=4)

        ttk.Label(tab, text="Save Name:").grid(row=9, column=0, sticky="w", padx=(10,4), pady=5)
        self.save_name_var = tk.StringVar(value="world1")
        ttk.Entry(tab, textvariable=self.save_name_var, width=16).grid(
            row=9, column=1, sticky="w", padx=4)
        ttk.Label(tab, text="(world save folder name)",
                  foreground=self.TEXT_DIM, font=("Segoe UI", 7)).grid(
            row=9, column=2, sticky="w", padx=4)

        self._section(tab, 10, "Visibility")

        self.list_steam_var = tk.BooleanVar(value=True)
        self.list_eos_var   = tk.BooleanVar(value=False)
        self.secure_var     = tk.BooleanVar(value=True)
        steam_chk = ttk.Checkbutton(tab, variable=self.list_steam_var, text="List on Steam server browser")
        steam_chk.grid(row=12, column=1, sticky="w", padx=4, pady=2)
        st_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        st_tip.grid(row=12, column=2, sticky="w", padx=4)
        self._bind_tooltip(st_tip, "Makes your server visible in the Steam in-game server browser so players can find it without knowing the IP")

        eos_chk = ttk.Checkbutton(tab, variable=self.list_eos_var, text="List on Epic Online Services (EOS)")
        eos_chk.grid(row=13, column=1, sticky="w", padx=4, pady=2)
        eos_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        eos_tip.grid(row=13, column=2, sticky="w", padx=4)
        self._bind_tooltip(eos_tip, "Lists server on Epic's network — only needed if players are joining via Epic Games Store version")

        sec_chk = ttk.Checkbutton(tab, variable=self.secure_var, text="Secure (VAC enabled)")
        sec_chk.grid(row=14, column=1, sticky="w", padx=4, pady=2)
        sec_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        sec_tip.grid(row=14, column=2, sticky="w", padx=4)
        self._bind_tooltip(sec_tip, "Enables Valve Anti-Cheat (VAC) — recommended to keep on. Disabling allows players with VAC bans to connect")

        self._section(tab, 15, "Performance & Saves")

        ttk.Label(tab, text="Server FPS:").grid(row=17, column=0, sticky="w", padx=(10,4), pady=5)
        self.server_fps_var = tk.IntVar(value=30)
        ttk.Spinbox(tab, from_=10, to=60, textvariable=self.server_fps_var, width=8).grid(
            row=17, column=1, sticky="w", padx=4)
        fps_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        fps_tip.grid(row=17, column=2, sticky="w", padx=4)
        self._bind_tooltip(fps_tip, "Server simulation tick rate. 30 is default and recommended — higher uses more CPU with little benefit")

        ttk.Label(tab, text="Max Connected Admins:").grid(row=18, column=0, sticky="w", padx=(10,4), pady=5)
        self.max_admins_var = tk.IntVar(value=4)
        ttk.Spinbox(tab, from_=1, to=10, textvariable=self.max_admins_var, width=8).grid(
            row=18, column=1, sticky="w", padx=4)
        adm_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        adm_tip.grid(row=18, column=2, sticky="w", padx=4)
        self._bind_tooltip(adm_tip, "How many admin-slot connections are reserved — admins can join even when the server is full")

        self.autosave_var = tk.IntVar(value=120)
        self._slider_row(tab, 19, "Auto-Save Interval (sec)", self.autosave_var,
                         30, 600, 10, "{:.0f}", "s",
                         "How often the server writes a save to disk — lower = less data lost on crash, higher = better performance")

        ttk.Label(tab, text="Auto-Save Count:").grid(row=20, column=0, sticky="w", padx=(10,4), pady=5)
        self.autosave_count_var = tk.IntVar(value=20)
        ttk.Spinbox(tab, from_=1, to=100, textvariable=self.autosave_count_var, width=8).grid(
            row=20, column=1, sticky="w", padx=4)
        asc_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        asc_tip.grid(row=20, column=2, sticky="w", padx=4)
        self._bind_tooltip(asc_tip, "Number of rolling save slots kept on disk — older saves are deleted as new ones are written. More slots = more disk space used")

        self.compress_saves_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(tab, variable=self.compress_saves_var,
                        text="Compress save files").grid(
            row=21, column=1, sticky="w", padx=4, pady=2)
        cmp_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        cmp_tip.grid(row=21, column=2, sticky="w", padx=4)
        self._bind_tooltip(cmp_tip, "Compresses save files to save disk space — recommended to keep enabled")

        self._section(tab, 22, "RCON (Remote Console)")
        self.rcon_enabled_var = tk.BooleanVar()
        ttk.Checkbutton(tab, variable=self.rcon_enabled_var, text="Enable RCON").grid(
            row=24, column=1, sticky="w", padx=4)
        rcon_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        rcon_tip.grid(row=24, column=2, sticky="w", padx=4)
        self._bind_tooltip(rcon_tip, "Enables remote console access for sending commands like announcements and scheduled shutdowns from the Admin tab")

        ttk.Label(tab, text="RCON Port:").grid(row=25, column=0, sticky="w", padx=(10,4), pady=5)
        self.rcon_port_var = tk.IntVar(value=25575)
        ttk.Spinbox(tab, from_=1024, to=65535, textvariable=self.rcon_port_var, width=10).grid(
            row=25, column=1, sticky="w", padx=4)
        rp_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 9), cursor="question_arrow")
        rp_tip.grid(row=25, column=2, sticky="w", padx=4)
        self._bind_tooltip(rp_tip, "Port the RCON server listens on — only needs to be accessible locally (127.0.0.1), no router forwarding needed")

        ttk.Label(tab, text="RCON Password:").grid(row=26, column=0, sticky="w", padx=(10,4), pady=5)
        self.rcon_password_var = tk.StringVar()
        self._password_entry(tab, self.rcon_password_var, width=24).grid(
            row=26, column=1, sticky="w", padx=4)

        ttk.Label(tab, text="(Required for the Admin tab to query live players)",
                  foreground=self.TEXT_DIM, font=("Segoe UI", 7)).grid(
            row=27, column=1, sticky="w", padx=4)

    # ── Tab: Game Settings ──────────────────────────────────────────────────
    def _build_tab_game(self):
        tab = self._scrollable_tab("  Game  ")
        tab.columnconfigure(1, weight=1)

        self._section(tab, 0, "Day / Night Cycle  (stored in GameTimeModifiers)")

        # Total cycle length — text entry in minutes
        self.day_len_var   = tk.DoubleVar(value=360)   # total cycle minutes
        self.day_start_var = tk.DoubleVar(value=9)
        self.day_end_var   = tk.DoubleVar(value=17)
        self.night_len_var = tk.DoubleVar(value=180)   # kept for compat, not shown

        ttk.Label(tab, text="Total Cycle Length (min):", width=28, anchor="w").grid(
            row=2, column=0, sticky="w", padx=(10,4), pady=5)
        self.cycle_entry_var = tk.StringVar()
        cycle_entry = ttk.Entry(tab, textvariable=self.cycle_entry_var, width=10)
        cycle_entry.grid(row=2, column=1, sticky="w", padx=4)
        ttk.Label(tab, text="minutes  (e.g. 360 = 6 hours real time)",
                  foreground=self.TEXT_DIM, font=("Segoe UI", 7)).grid(
            row=2, column=2, sticky="w", padx=4)

        self._slider_row(tab, 3, "Day Start (hour)", self.day_start_var, 0, 23, 1, "{:.0f}", "h")
        self._slider_row(tab, 4, "Day End (hour)",   self.day_end_var,   0, 23, 1, "{:.0f}", "h")

        # Calculated display
        info_frame = tk.Frame(tab, bg=self.ACCENT2, padx=10, pady=6)
        info_frame.grid(row=5, column=0, columnspan=4, sticky="ew", padx=10, pady=(4,2))
        self.cycle_info_lbl = tk.Label(info_frame,
            text="", bg=self.ACCENT2, fg=self.TEXT,
            font=("Consolas", 8), justify="left")
        self.cycle_info_lbl.pack(anchor="w")

        # Wire up live recalculation
        for v in (self.day_start_var, self.day_end_var):
            v.trace_add("write", lambda *_: self._recalc_cycle())
        self.cycle_entry_var.trace_add("write", lambda *_: self._recalc_cycle())
        # Initialise display after a short delay so widgets exist
        self.after(100, self._recalc_cycle)

        self._section(tab, 6, "Blood Moon  (stored in GameTimeModifiers)")
        self.bm_freq_min_var = tk.IntVar()
        self.bm_freq_max_var = tk.IntVar()
        self.bm_dur_var      = tk.DoubleVar()
        self._slider_row(tab, 8,  "Blood Moon Freq Min (days)", self.bm_freq_min_var, 1, 30, 1, "{:.0f}", " days",
                         "Minimum number of in-game days between blood moons")
        self._slider_row(tab, 9,  "Blood Moon Freq Max (days)", self.bm_freq_max_var, 1, 30, 1, "{:.0f}", " days",
                         "Maximum number of in-game days between blood moons — actual timing is random between min and max")
        self._slider_row(tab, 10, "Blood Moon Buff",            self.bm_dur_var, 0.0, 1.0, 0.05, "{:.2f}", "x",
                         "Strength of the blood moon buff given to players during the event (game enforces 0–1)")

        self._section(tab, 11, "Castle")
        self.decay_var  = tk.DoubleVar()
        self.drain_var  = tk.DoubleVar()
        self._slider_row(tab, 13, "Castle Decay Rate",        self.decay_var, 0.0, 5.0, 0.1, "{:.1f}", "x",
                         "How fast your castle deteriorates when not maintained — 0 = never decays")
        self._slider_row(tab, 14, "Blood Essence Drain Rate", self.drain_var, 0.01, 5.0, 0.01, "{:.2f}", "x",
                         "How fast blood essence drains from your castle heart — minimum 0.01 (game won't go lower)")

        self._section(tab, 15, "Resources & Economy")
        self.xp_var       = tk.DoubleVar()
        self.drop_var     = tk.DoubleVar()
        self.resource_var = tk.DoubleVar()
        self.shard_var    = tk.DoubleVar()
        self.blood_essence_yield_var = tk.DoubleVar()
        self.inventory_stacks_var    = tk.DoubleVar()
        self._slider_row(tab, 17, "XP Multiplier",       self.xp_var,                  0.1, 10.0, 0.1, "{:.2f}", "x",
                         "How fast players level up — higher = faster progression")
        self._slider_row(tab, 18, "Drop Table Modifier", self.drop_var,                0.1, 10.0, 0.1, "{:.2f}", "x",
                         "Multiplies loot from all enemy types — higher = more drops")
        self._slider_row(tab, 19, "Resource Yield",      self.resource_var,            0.1, 10.0, 0.1, "{:.2f}", "x",
                         "Multiplies resources gathered from the world (wood, stone, ore, etc)")
        self._slider_row(tab, 20, "Soul Shard Modifier", self.shard_var,               0.0,  5.0, 0.1, "{:.2f}", "x",
                         "Affects Soul Shard drop rates from VBlood bosses")
        self._slider_row(tab, 21, "Blood Essence Yield", self.blood_essence_yield_var, 0.1,  5.0, 0.1, "{:.1f}", "x",
                         "How much blood essence enemies drop — used to fuel your castle heart")
        self._slider_row(tab, 22, "Inventory Stacks",    self.inventory_stacks_var,    0.1,  5.0, 0.1, "{:.1f}", "x",
                         "Multiplies max stack size for items in your inventory")

        self._section(tab, 23, "Crafting & Building")
        self.build_cost_var      = tk.DoubleVar()
        self.craft_rate_var      = tk.DoubleVar()
        self.recipe_cost_var     = tk.DoubleVar()
        self.research_cost_var   = tk.DoubleVar()
        self.research_time_var   = tk.DoubleVar()
        self.refine_cost_var     = tk.DoubleVar()
        self.refine_rate_var     = tk.DoubleVar()
        self.dismantle_var       = tk.DoubleVar()
        self.repair_cost_var     = tk.DoubleVar()
        self._slider_row(tab, 25, "Build Cost",         self.build_cost_var,    0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Materials needed to place castle floors, walls, and structures")
        self._slider_row(tab, 26, "Craft Rate",         self.craft_rate_var,    0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Speed of crafting items — higher = faster production")
        self._slider_row(tab, 27, "Recipe Cost",        self.recipe_cost_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Ingredients required to craft items like weapons and armor")
        self._slider_row(tab, 28, "Research Cost",      self.research_cost_var, 0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Resources spent to unlock new crafting recipes")
        self._slider_row(tab, 29, "Research Time",      self.research_time_var, 0.1, 5.0, 0.1, "{:.1f}", "x",
                         "How long research takes — lower = faster unlocks")
        self._slider_row(tab, 30, "Refinement Cost",    self.refine_cost_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Raw materials needed to refine resources (e.g. ore to ingots)")
        self._slider_row(tab, 31, "Refinement Rate",    self.refine_rate_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Speed of refinement — higher = faster processing")
        self._slider_row(tab, 32, "Dismantle Resources",self.dismantle_var,     0.1, 2.0, 0.1, "{:.1f}", "x",
                         "How much you get back when dismantling structures — 1.0 = default return rate")
        self._slider_row(tab, 33, "Repair Cost",        self.repair_cost_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Materials needed to repair damaged equipment and structures")

        self._section(tab, 34, "Vampire Stats  (stored in VampireStatModifiers)")
        self.vamp_hp_var    = tk.DoubleVar()
        self.vamp_phys_var  = tk.DoubleVar()
        self.vamp_spell_var = tk.DoubleVar()
        self.vamp_move_var  = tk.DoubleVar()
        self._slider_row(tab, 36, "Max Health",     self.vamp_hp_var,    0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies player max HP — good for a more forgiving experience")
        self._slider_row(tab, 37, "Physical Power", self.vamp_phys_var,  0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies physical weapon damage dealt by players")
        self._slider_row(tab, 38, "Spell Power",    self.vamp_spell_var, 0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies spell and ability damage dealt by players")

        self._section(tab, 39, "Enemy Stats  (stored in UnitStatModifiers_Global)")
        self.enemy_hp_var    = tk.DoubleVar()
        self.enemy_power_var = tk.DoubleVar()
        self.enemy_level_var = tk.IntVar()
        self.vblood_hp_var   = tk.DoubleVar()
        self.vblood_pow_var  = tk.DoubleVar()
        self.vblood_lvl_var  = tk.IntVar()
        self._slider_row(tab, 41, "Enemy Max Health",     self.enemy_hp_var,    0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies HP of all non-boss enemies. 2x = twice as tanky")
        self._slider_row(tab, 42, "Enemy Power",          self.enemy_power_var, 0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies damage dealt by all non-boss enemies. 2x = hits twice as hard")
        self._slider_row(tab, 43, "Enemy Level Increase", self.enemy_level_var, 0,   20,  1,   "{:.0f}", "",
                         "Adds flat levels to all enemies — makes gear requirements stricter")
        self._slider_row(tab, 44, "VBlood Max Health",    self.vblood_hp_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies HP of V Blood bosses only. Independent from regular enemies")
        self._slider_row(tab, 45, "VBlood Power",         self.vblood_pow_var,  0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies damage dealt by V Blood bosses only")
        self._slider_row(tab, 46, "VBlood Level Increase",self.vblood_lvl_var,  0,   20,  1,   "{:.0f}", "",
                         "Adds flat levels to V Blood bosses — scales their difficulty independently")

        self._section(tab, 47, "Trader  (stored in TraderModifiers)")
        self.trader_stock_var   = tk.DoubleVar()
        self.trader_price_var   = tk.DoubleVar()
        self.trader_restock_var = tk.DoubleVar()
        self._slider_row(tab, 49, "Stock Modifier",   self.trader_stock_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "How much stock traders carry — higher = more items available")
        self._slider_row(tab, 50, "Price Modifier",   self.trader_price_var,   0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies trader prices — lower = cheaper, higher = more expensive")
        self._slider_row(tab, 51, "Restock Timer",    self.trader_restock_var, 0.1, 5.0, 0.1, "{:.1f}", "x",
                         "How fast traders restock — lower = restocks faster")

    # ── Tab: Player Settings ────────────────────────────────────────────────
    def _recalc_cycle(self):
        """Recalculate and display day/night lengths from cycle total and start/end hours."""
        try:
            total_min = float(self.cycle_entry_var.get())
            start_h   = float(self.day_start_var.get())
            end_h     = float(self.day_end_var.get())
            total_sec = total_min * 60

            if end_h > start_h:
                day_frac  = (end_h - start_h) / 24
            else:
                day_frac  = (24 - start_h + end_h) / 24

            day_sec   = total_sec * day_frac
            night_sec = total_sec * (1 - day_frac)
            day_min   = day_sec / 60
            night_min = night_sec / 60

            # Update internal vars for saving
            self.day_len_var.set(total_min)
            self.night_len_var.set(night_min)

            def fmt(m):
                h, mn = int(m) // 60, int(m) % 60
                return f"{h}h {mn:02d}m  ({m:.0f} min)"

            self.cycle_info_lbl.config(
                text=f"  Day length:    {fmt(day_min)}\n"
                     f"  Night length:  {fmt(night_min)}\n"
                     f"  Total cycle:   {fmt(total_min)}")
        except (ValueError, AttributeError):
            pass

    def _build_tab_player(self):
        tab = self._scrollable_tab("  Players  ")
        tab.columnconfigure(1, weight=1)

        self._section(tab, 0, "Players")
        self.max_players_var = tk.IntVar()
        self._slider_row(tab, 2, "Max Players", self.max_players_var, 1, 40, 1, "{:.0f}", "",
                         "Maximum number of players that can be connected at the same time")

        ttk.Label(tab, text="PvP Enabled:").grid(row=3, column=0, sticky="w", padx=(10,4), pady=5)
        self.pvp_var = tk.BooleanVar()
        ttk.Checkbutton(tab, variable=self.pvp_var, text="Allow PvP combat").grid(
            row=3, column=1, sticky="w", padx=4)

        self._section(tab, 4, "Combat & Damage")
        self.pvp_dmg_var = tk.DoubleVar()
        self._slider_row(tab, 6, "PvP Damage Modifier", self.pvp_dmg_var, 0.1, 5.0, 0.1, "{:.1f}", "x",
                         "Multiplies damage players deal to each other — lower = more forgiving PvP")

        self._section(tab, 7, "Servants & Progression")
        self.servant_var     = tk.DoubleVar()
        self.blood_start_var = tk.IntVar()
        self._slider_row(tab, 9,  "Servant Convert Rate",   self.servant_var,     0.1, 5.0, 0.1, "{:.1f}", "x",
                         "How fast humans are converted into servants — higher = quicker conversion")

        ttk.Label(tab, text="Starting Blood Essence:", width=28, anchor="w").grid(
            row=10, column=0, sticky="w", padx=(10,4), pady=5)
        self.blood_start_var = tk.IntVar(value=100)
        ttk.Spinbox(tab, from_=0, to=50000, textvariable=self.blood_start_var,
                    width=10, increment=100).grid(row=10, column=1, sticky="w", padx=4)
        tip_lbl = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        tip_lbl.grid(row=10, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(tip_lbl,
            "Amount of blood essence each player starts with on a new character.\n\n"
            "Default (vanilla): 100\n"
            "A full castle heart holds around 2500\n"
            "Relaxed preset: around 500\n\n"
            "Higher values let new players get their castle started faster\n"
            "without hunting for blood essence right away.")

        self._section(tab, 11, "Item & Loot Rules")

        self.teleport_bound_var   = tk.BooleanVar(value=True)
        self.blood_bound_var      = tk.BooleanVar(value=True)
        self.bat_bound_var        = tk.BooleanVar(value=False)
        self.loot_containers_var  = tk.BooleanVar(value=True)

        def _chk_row(parent, row, var, label, tip):
            ttk.Checkbutton(parent, variable=var, text=label).grid(
                row=row, column=1, sticky="w", padx=4, pady=2)
            t = tk.Label(parent, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                         font=("Segoe UI", 9), cursor="question_arrow")
            t.grid(row=row, column=3, sticky="w", padx=(0,6))
            self._bind_tooltip(t, tip)

        _chk_row(tab, 13, self.teleport_bound_var,
                 "Teleport Bound Items",
                 "When enabled, players cannot teleport while carrying items that are\n"
                 "flagged as teleport-bound (most resources and gear).\n"
                 "Disable to allow free teleporting with any items.\n\n"
                 "Default: enabled (more challenging — encourages planning routes)")

        _chk_row(tab, 14, self.blood_bound_var,
                 "Blood Bound Equipment",
                 "When enabled, equipped items drop on death but are bound to the player\n"
                 "and can only be picked up by them.\n"
                 "Disable to let anyone loot your gear on death (harsher PvP).\n\n"
                 "Default: enabled")

        _chk_row(tab, 15, self.bat_bound_var,
                 "Bat Form Bound Items",
                 "When enabled, players cannot carry items while in bat form.\n"
                 "Disable to allow carrying items as a bat.\n\n"
                 "Default: disabled")

        _chk_row(tab, 16, self.loot_containers_var,
                 "Can Loot Enemy Containers",
                 "When enabled, players can loot chests and containers inside\n"
                 "enemy-held locations.\n"
                 "Disable to make exploration less rewarding.\n\n"
                 "Default: enabled")

        self._section(tab, 17, "Social & Clans")

        self.global_chat_var       = tk.BooleanVar(value=True)
        self.all_waypoints_var     = tk.BooleanVar(value=False)

        _chk_row(tab, 19, self.global_chat_var,
                 "Allow Global Chat",
                 "Enables the global chat channel all players can see.\n"
                 "Disable for a more isolated or immersive experience.\n\n"
                 "Default: enabled")

        _chk_row(tab, 20, self.all_waypoints_var,
                 "All Waypoints Unlocked",
                 "When enabled, all teleport waypoints are unlocked for everyone\n"
                 "from the start without needing to discover them.\n\n"
                 "Default: disabled")

        ttk.Label(tab, text="Clan Size:", width=28, anchor="w").grid(
            row=21, column=0, sticky="w", padx=(10,4), pady=5)
        self.clan_size_var = tk.IntVar(value=4)
        ttk.Spinbox(tab, from_=1, to=10, textvariable=self.clan_size_var, width=6).grid(
            row=21, column=1, sticky="w", padx=4)
        cs_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                          font=("Segoe UI", 9), cursor="question_arrow")
        cs_tip.grid(row=21, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(cs_tip,
            "Maximum number of players that can be in the same clan.\n"
            "Clan members share map progress and can build castles together.\n\n"
            "Default: 4")

        self._section(tab, 22, "Castle Rules")

        self.castle_reloc_var      = tk.BooleanVar(value=True)
        self.free_castle_claim_var = tk.BooleanVar(value=False)
        self.free_castle_raid_var  = tk.BooleanVar(value=False)
        self.free_castle_dest_var  = tk.BooleanVar(value=False)

        _chk_row(tab, 24, self.castle_reloc_var,
                 "Castle Relocation Enabled",
                 "Allows players to pick up and relocate their entire castle.\n\n"
                 "Default: enabled")

        _chk_row(tab, 25, self.free_castle_claim_var,
                 "Free Castle Claim",
                 "When enabled, players can claim abandoned castles for free\n"
                 "without spending resources.\n\n"
                 "Default: disabled")

        _chk_row(tab, 26, self.free_castle_raid_var,
                 "Free Castle Raid",
                 "When enabled, anyone can raid any castle at any time\n"
                 "without needing a siege weapon.\n\n"
                 "Default: disabled")

        _chk_row(tab, 27, self.free_castle_dest_var,
                 "Free Castle Destroy",
                 "When enabled, anyone can destroy any castle for free.\n\n"
                 "Default: disabled")

        ttk.Label(tab, text="Castle Reloc Cooldown (s):", width=28, anchor="w").grid(
            row=28, column=0, sticky="w", padx=(10,4), pady=5)
        self.castle_reloc_cooldown_var = tk.IntVar(value=10800)
        ttk.Spinbox(tab, from_=0, to=86400, textvariable=self.castle_reloc_cooldown_var,
                    width=10, increment=600).grid(row=28, column=1, sticky="w", padx=4)
        crc_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        crc_tip.grid(row=28, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(crc_tip,
            "How long (in seconds) before a player can relocate their castle again.\n"
            "Default: 10800 (3 hours)\n0 = no cooldown")

        ttk.Label(tab, text="Castle Min Distance (floors):", width=28, anchor="w").grid(
            row=29, column=0, sticky="w", padx=(10,4), pady=5)
        self.castle_min_dist_var = tk.IntVar(value=2)
        ttk.Spinbox(tab, from_=0, to=20, textvariable=self.castle_min_dist_var, width=6).grid(
            row=29, column=1, sticky="w", padx=4)
        cmd_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        cmd_tip.grid(row=29, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(cmd_tip,
            "Minimum distance in floor tiles between two castle hearts.\n"
            "Prevents players from building castles right next to each other.\n\n"
            "Default: 2")

        self._section(tab, 30, "Death & Disconnection")

        self.inactivity_kill_var   = tk.BooleanVar(value=True)
        self.disconnected_dead_var = tk.BooleanVar(value=True)

        _chk_row(tab, 32, self.inactivity_kill_var,
                 "Inactivity Kill Enabled",
                 "When enabled, player characters are removed from the world\n"
                 "after being inactive for the configured time period.\n"
                 "Prevents abandoned characters from cluttering the server.\n\n"
                 "Default: enabled")

        _chk_row(tab, 33, self.disconnected_dead_var,
                 "Disable Disconnected Dead",
                 "When enabled, players who disconnect while dead are removed\n"
                 "from the world after the timer expires.\n\n"
                 "Default: enabled")

        ttk.Label(tab, text="Disconnected Dead Timer (s):", width=28, anchor="w").grid(
            row=34, column=0, sticky="w", padx=(10,4), pady=5)
        self.disconnected_dead_timer_var = tk.IntVar(value=60)
        ttk.Spinbox(tab, from_=0, to=3600, textvariable=self.disconnected_dead_timer_var,
                    width=8, increment=10).grid(row=34, column=1, sticky="w", padx=4)
        ddt_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        ddt_tip.grid(row=34, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(ddt_tip,
            "Seconds before a disconnected dead player is removed from the world.\n"
            "Default: 60")

        ttk.Label(tab, text="Sun Immunity on Disconnect (s):", width=28, anchor="w").grid(
            row=35, column=0, sticky="w", padx=(10,4), pady=5)
        self.disconnect_sun_var = tk.IntVar(value=300)
        ttk.Spinbox(tab, from_=0, to=3600, textvariable=self.disconnect_sun_var,
                    width=8, increment=30).grid(row=35, column=1, sticky="w", padx=4)
        dsi_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        dsi_tip.grid(row=35, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(dsi_tip,
            "How long (seconds) a disconnected player is immune to sun damage.\n"
            "Protects players who get disconnected while exposed.\n\n"
            "Default: 300 (5 minutes)")

        ttk.Label(tab, text="Starting Progression Level:", width=28, anchor="w").grid(
            row=36, column=0, sticky="w", padx=(10,4), pady=5)
        self.starting_level_var = tk.IntVar(value=0)
        ttk.Spinbox(tab, from_=0, to=90, textvariable=self.starting_level_var,
                    width=6, increment=1).grid(row=36, column=1, sticky="w", padx=4)
        sl_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                          font=("Segoe UI", 9), cursor="question_arrow")
        sl_tip.grid(row=36, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(sl_tip,
            "Gear/progression level new characters start at.\n"
            "0 = start from the beginning (default)\n"
            "Higher values let new players skip early content and catch up\n"
            "to friends who are further along.")

        self._section(tab, 37, "PvP Interaction Windows")
        ttk.Label(tab,
            text="These control when PvP raiding and castle attacks are allowed.\n"
                 "Times use 24-hour format. Only applies when PvP mode is enabled.",
            foreground=self.TEXT_DIM,
            font=("Segoe UI", 7), justify="left").grid(
            row=38, column=0, columnspan=4, sticky="w", padx=12, pady=(2,4))

        for row, label, start_var_name, end_var_name in [
            (39, "Player vs Player — Weekday",  "pvp_player_wday_start", "pvp_player_wday_end"),
            (40, "Player vs Player — Weekend",  "pvp_player_wend_start", "pvp_player_wend_end"),
            (41, "Castle Siege — Weekday",      "pvp_castle_wday_start", "pvp_castle_wday_end"),
            (42, "Castle Siege — Weekend",      "pvp_castle_wend_start", "pvp_castle_wend_end"),
        ]:
            setattr(self, start_var_name, tk.IntVar(value=20))
            setattr(self, end_var_name,   tk.IntVar(value=22))
            ttk.Label(tab, text=label + ":", width=28, anchor="w").grid(
                row=row, column=0, sticky="w", padx=(10,4), pady=3)
            f = tk.Frame(tab, bg=self.PANEL_BG)
            f.grid(row=row, column=1, sticky="w", padx=4)
            ttk.Spinbox(f, from_=0, to=23, textvariable=getattr(self, start_var_name),
                        width=4).pack(side="left")
            tk.Label(f, text=" : 00  to  ", bg=self.PANEL_BG,
                     fg=self.TEXT_DIM, font=("Segoe UI", 8)).pack(side="left")
            ttk.Spinbox(f, from_=0, to=23, textvariable=getattr(self, end_var_name),
                        width=4).pack(side="left")
            tk.Label(f, text=" : 00", bg=self.PANEL_BG,
                     fg=self.TEXT_DIM, font=("Segoe UI", 8)).pack(side="left")

        self._section(tab, 43, "PvP Protection & Death")

        ttk.Label(tab, text="PvP Protection Mode:", width=28, anchor="w").grid(
            row=45, column=0, sticky="w", padx=(10,4), pady=5)
        self.pvp_protection_var = tk.StringVar(value="Medium")
        ttk.Combobox(tab, textvariable=self.pvp_protection_var, width=12,
                     values=["Disabled", "Short", "Medium", "Long"],
                     state="readonly").grid(row=45, column=1, sticky="w", padx=4)
        pp_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                          font=("Segoe UI", 9), cursor="question_arrow")
        pp_tip.grid(row=45, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(pp_tip,
            "How long new players are protected from PvP after joining.\n"
            "Short = brief window, Medium = moderate, Long = extended protection.\n\n"
            "Default: Medium")

        ttk.Label(tab, text="Death Container Permission:", width=28, anchor="w").grid(
            row=46, column=0, sticky="w", padx=(10,4), pady=5)
        self.death_container_var = tk.StringVar(value="Anyone")
        ttk.Combobox(tab, textvariable=self.death_container_var, width=16,
                     values=["Anyone", "Clan", "OnlySelf"],
                     state="readonly").grid(row=46, column=1, sticky="w", padx=4)
        dc_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                          font=("Segoe UI", 9), cursor="question_arrow")
        dc_tip.grid(row=46, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(dc_tip,
            "Who can loot the bag dropped when a player dies.\n"
            "Anyone = any player, Clan = only clan members, OnlySelf = only you.\n\n"
            "Default: Anyone")

        ttk.Label(tab, text="Inventory Drop on Death:", width=28, anchor="w").grid(
            row=47, column=0, sticky="w", padx=(10,4), pady=5)
        self.inventory_drop_var = tk.StringVar(value="Always")
        ttk.Combobox(tab, textvariable=self.inventory_drop_var, width=16,
                     values=["Always", "Never", "OnlyEquipped"],
                     state="readonly").grid(row=47, column=1, sticky="w", padx=4)
        inv_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        inv_tip.grid(row=47, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(inv_tip,
            "Controls whether your backpack (inventory) drops when you die.\n"
            "Always = your bag drops every death (default, items can be lost if server restarts)\n"
            "Never = nothing drops — you keep everything on death\n"
            "OnlyEquipped = only your equipped gear drops, not your bag contents\n\n"
            "Default: Always")

        self._section(tab, 48, "Siege Weapons")

        ttk.Label(tab, text="Siege Weapon Health:", width=28, anchor="w").grid(
            row=49, column=0, sticky="w", padx=(10,4), pady=5)
        self.siege_weapon_health_var = tk.StringVar(value="Normal")
        ttk.Combobox(tab, textvariable=self.siege_weapon_health_var, width=12,
                     values=["Normal", "High", "VeryHigh", "Low"],
                     state="readonly").grid(row=49, column=1, sticky="w", padx=4)
        swh_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        swh_tip.grid(row=49, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(swh_tip,
            "How much health siege weapons have during castle raids.\n"
            "Higher = harder to destroy, longer sieges.\n\n"
            "Default: Normal")

        self.announce_siege_var    = tk.BooleanVar(value=True)
        self.show_siege_icon_var   = tk.BooleanVar(value=False)

        _chk_row(tab, 50, self.announce_siege_var,
                 "Announce Siege Weapon Spawn",
                 "Server announces to all players when a siege weapon is deployed.\n\n"
                 "Default: enabled")

        _chk_row(tab, 51, self.show_siege_icon_var,
                 "Show Siege Weapon Map Icon",
                 "Shows siege weapon locations on the map for all players.\n\n"
                 "Default: disabled")

        self._section(tab, 52, "War Events")

        ttk.Label(tab, text="War Event Interval:", width=28, anchor="w").grid(
            row=54, column=0, sticky="w", padx=(10,4), pady=5)
        self.war_event_interval_var = tk.IntVar(value=0)
        ttk.Spinbox(tab, from_=0, to=168, textvariable=self.war_event_interval_var,
                    width=6, increment=1).grid(row=54, column=1, sticky="w", padx=4)
        wei_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                           font=("Segoe UI", 9), cursor="question_arrow")
        wei_tip.grid(row=54, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(wei_tip,
            "How often (in hours) war events occur.\n"
            "0 = war events disabled.\n\n"
            "Default: 0 (disabled)")

        self._section(tab, 55, "Relics")

        ttk.Label(tab, text="Relic Spawn Type:", width=28, anchor="w").grid(
            row=57, column=0, sticky="w", padx=(10,4), pady=5)
        self.relic_spawn_var = tk.StringVar(value="Unique")
        ttk.Combobox(tab, textvariable=self.relic_spawn_var, width=16,
                     values=["Unique", "UniquePerPlayer", "Plentiful"],
                     state="readonly").grid(row=57, column=1, sticky="w", padx=4)
        rs_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                          font=("Segoe UI", 9), cursor="question_arrow")
        rs_tip.grid(row=57, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(rs_tip,
            "Controls how Soul Shards (relics) spawn in the world.\n"
            "Unique = only one of each exists, UniquePerPlayer = one per player,\n"
            "Plentiful = multiple can exist.\n\n"
            "Default: Unique")

        self._section(tab, 58, "Preset")
        ttk.Label(tab, text="Global Preset:").grid(row=60, column=0, sticky="w", padx=(10,4), pady=5)
        self.preset_var = tk.StringVar()
        preset_cb = ttk.Combobox(tab, textvariable=self.preset_var, width=20,
                                 values=["", "Standard", "Relaxed", "Difficult", "Brutal"],
                                 state="readonly")
        preset_cb.grid(row=60, column=1, sticky="w", padx=4)
        pr_tip = tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                          font=("Segoe UI", 9), cursor="question_arrow")
        pr_tip.grid(row=60, column=3, sticky="w", padx=(0,6))
        self._bind_tooltip(pr_tip,
            "Applies a server-side difficulty preset on next start.\n"
            "⚠ The preset overrides many individual settings in ServerGameSettings.json.\n"
            "Leave blank to use your custom settings instead.\n\n"
            "Default: blank (use custom settings)")

    # ── Tab: Network ────────────────────────────────────────────────────────
    def _build_tab_network(self):
        tab = self._scrollable_tab("  Network  ")
        tab.columnconfigure(1, weight=1)

        self._section(tab, 0, "Ports")
        self.game_port_var  = tk.IntVar()
        self.query_port_var = tk.IntVar()

        ttk.Label(tab, text="Game Port:").grid(row=2, column=0, sticky="w", padx=(10,4), pady=5)
        ttk.Spinbox(tab, from_=1024, to=65535, textvariable=self.game_port_var, width=10).grid(
            row=2, column=1, sticky="w", padx=4)
        tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                 font=("Segoe UI", 9), cursor="question_arrow").grid(row=2, column=2, sticky="w", padx=4)
        self._bind_tooltip(tab.grid_slaves(row=2, column=2)[0],
                           "UDP port players connect to. Must be forwarded on your router. Default: 9876\n\n⚠ Changing from the default may stop your server appearing in the Steam/Epic server browser.")

        ttk.Label(tab, text="Query Port:").grid(row=3, column=0, sticky="w", padx=(10,4), pady=5)
        ttk.Spinbox(tab, from_=1024, to=65535, textvariable=self.query_port_var, width=10).grid(
            row=3, column=1, sticky="w", padx=4)
        tk.Label(tab, text="ℹ", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                 font=("Segoe UI", 9), cursor="question_arrow").grid(row=3, column=2, sticky="w", padx=4)
        self._bind_tooltip(tab.grid_slaves(row=3, column=2)[0],
                           "UDP port used by Steam server browser to list your server. Default: 9877. Also forward this on your router.\n\n⚠ Changing from the default may stop your server appearing in the Steam/Epic server browser.")

        self._section(tab, 5, "Info")
        info_text = (
            "• Forward both ports (UDP) on your router to this PC's local IP\n"
            "• Default Game Port : 9876 (UDP)\n"
            "• Default Query Port: 9877 (UDP)\n"
            "• Steam server browser also uses port 27015 (UDP)\n"
            "• Your local IP is usually 192.168.x.x — check ipconfig in Command Prompt\n\n"
            "⚠  Using non-default ports may prevent your server from appearing\n"
            "    in the Steam or Epic server browser list. Players can still connect\n"
            "    directly via IP:Port but won't find it by browsing."
        )
        tk.Label(tab, text=info_text, bg=self.PANEL_BG, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8), justify="left").grid(
            row=7, column=0, columnspan=4, sticky="w", padx=14, pady=4)

    # ── Tab: Admin ──────────────────────────────────────────────────────────
    def _build_tab_admin(self):
        outer = ttk.Frame(self.notebook)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(2, weight=1)
        outer.rowconfigure(4, weight=1)
        self.notebook.add(outer, text="  Admin  ")

        # ── Connected players ──
        self._section_plain(outer, 0, "Connected Players  (requires RCON enabled + server running)")
        btn_frame = tk.Frame(outer, bg=self.PANEL_BG)
        btn_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,4))

        tk.Button(btn_frame, text="⟳  Refresh Players", command=self._refresh_players,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left")
        self.rcon_status_lbl = tk.Label(btn_frame, text="", bg=self.PANEL_BG,
                                         fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.rcon_status_lbl.pack(side="left", padx=10)

        # Player list frame
        player_frame = tk.Frame(outer, bg=self.PANEL_BG)
        player_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0,8))
        player_frame.columnconfigure(0, weight=1)

        self.player_list_frame = tk.Frame(player_frame, bg=self.PANEL_BG)
        self.player_list_frame.pack(fill="both", expand=True)
        tk.Label(self.player_list_frame, text="Click Refresh Players to query the server.",
                 bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 8)).pack(padx=10, pady=10)

        # ── Admin list ──
        self._section_plain(outer, 3, "Admin List  (adminlist.txt  —  one Steam ID per line)")
        admin_frame = tk.Frame(outer, bg=self.PANEL_BG)
        admin_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0,4))
        admin_frame.columnconfigure(0, weight=1)
        admin_frame.rowconfigure(0, weight=1)

        self.admin_text = tk.Text(admin_frame, bg="#0d1b2a", fg=self.TEXT,
                                   insertbackground=self.TEXT, font=("Consolas", 9),
                                   relief="flat", height=8, width=40)
        self.admin_text.grid(row=0, column=0, sticky="nsew")
        sb = ttk.Scrollbar(admin_frame, orient="vertical", command=self.admin_text.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.admin_text.configure(yscrollcommand=sb.set)

        btn2 = tk.Frame(outer, bg=self.PANEL_BG)
        btn2.grid(row=5, column=0, sticky="ew", padx=10, pady=(2,8))
        tk.Button(btn2, text="📂  Load adminlist.txt", command=self._load_adminlist,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0,6))
        tk.Button(btn2, text="💾  Save adminlist.txt", command=self._save_adminlist,
                  bg=self.GREEN, fg="#0d1b2a", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left", padx=(0,6))
        tk.Button(btn2, text="ℹ  How to activate admin", command=self._show_admin_instructions,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=4, cursor="hand2").pack(side="left")

        # ── Raw RCON console ──
        self._section_plain(outer, 6, "RCON Console  (send any command directly)")
        console_frame = tk.Frame(outer, bg=self.PANEL_BG)
        console_frame.grid(row=7, column=0, sticky="nsew", padx=10, pady=(0,4))
        console_frame.columnconfigure(0, weight=1)
        outer.rowconfigure(7, weight=1)

        self.rcon_output = tk.Text(console_frame, bg="#0a1020", fg=self.GREEN,
                                    insertbackground=self.GREEN, font=("Consolas", 8),
                                    relief="flat", height=6, state="disabled")
        self.rcon_output.grid(row=0, column=0, sticky="nsew")
        csb = ttk.Scrollbar(console_frame, orient="vertical", command=self.rcon_output.yview)
        csb.grid(row=0, column=1, sticky="ns")
        self.rcon_output.configure(yscrollcommand=csb.set)

        cmd_row = tk.Frame(outer, bg=self.PANEL_BG)
        cmd_row.grid(row=8, column=0, sticky="ew", padx=10, pady=(2,10))
        cmd_row.columnconfigure(0, weight=1)
        self.rcon_cmd_var = tk.StringVar()
        cmd_entry = ttk.Entry(cmd_row, textvariable=self.rcon_cmd_var, font=("Consolas", 9))
        cmd_entry.grid(row=0, column=0, sticky="ew", padx=(0,6))
        cmd_entry.bind("<Return>", lambda e: self._send_rcon_console())
        tk.Button(cmd_row, text="Send", command=self._send_rcon_console,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=3, cursor="hand2").grid(row=0, column=1)

    def _section_plain(self, parent, row, text):
        """Section header for non-grid (place/pack) parents."""
        tk.Frame(parent, bg=self.ACCENT2, height=2).grid(
            row=row, column=0, sticky="ew", padx=10, pady=(10,0))
        tk.Label(parent, text=text, bg=self.PANEL_BG, fg=self.ACCENT,
                 font=("Segoe UI", 9, "bold")).grid(
            row=row, column=0, sticky="w", padx=14, pady=(2,2))

    # ── RCON client ─────────────────────────────────────────────────────────
    def _rcon_send(self, command):
        """
        Minimal RCON client (Valve RCON protocol).
        Returns the response string, or raises an exception on failure.
        """
        host     = "127.0.0.1"
        port     = self.cfg.get("rcon_port", 25575)
        password = self.cfg.get("rcon_password", "")

        def _pack(req_id, req_type, body):
            data = body.encode("utf-8") + b"\x00\x00"
            header = struct.pack("<iii", len(data) + 8, req_id, req_type)
            return header + data

        def _recv_packet(sock):
            raw_len = b""
            while len(raw_len) < 4:
                chunk = sock.recv(4 - len(raw_len))
                if not chunk:
                    raise ConnectionError("Connection closed")
                raw_len += chunk
            length = struct.unpack("<i", raw_len)[0]
            raw = b""
            while len(raw) < length:
                chunk = sock.recv(length - len(raw))
                if not chunk:
                    raise ConnectionError("Connection closed")
                raw += chunk
            req_id, resp_type = struct.unpack("<ii", raw[:8])
            body = raw[8:].rstrip(b"\x00")
            return req_id, resp_type, body.decode("utf-8", errors="replace")

        with socket.create_connection((host, port), timeout=5) as s:
            # Auth
            s.sendall(_pack(1, 3, password))
            rid, rtype, _ = _recv_packet(s)
            if rid == -1:
                raise PermissionError("RCON authentication failed — check password")
            # Command
            s.sendall(_pack(2, 2, command))
            _, _, response = _recv_packet(s)
            return response

    def _refresh_players(self):
        """Parse the server log to find players who connected since the last server start."""
        # Don't read the log if the server isn't running — results would be from last session
        if not self.server_process and not self._find_server_process():
            self.rcon_status_lbl.config(text="Server is not running — start the server first.", fg=self.ACCENT)
            for w in self.player_list_frame.winfo_children():
                w.destroy()
            tk.Label(self.player_list_frame,
                     text="Server is not running.\nStart the server, then click Refresh Players.",
                     bg=self.PANEL_BG, fg=self.TEXT_DIM,
                     font=("Segoe UI", 8), justify="center").pack(padx=10, pady=14)
            return

        self.rcon_status_lbl.config(text="Reading log…", fg=self.YELLOW)
        self.update_idletasks()

        base = os.path.normpath(self.path_var.get().strip())
        # V Rising log locations to try
        log_candidates = [
            os.path.join(base, "logs", "VRisingServer.log"),
            os.path.join(base, "VRisingServer_Data", "logs", "VRisingServer.log"),
            os.path.expandvars(r"%USERPROFILE%\AppData\LocalLow\Stunlock Studios\VRisingServer\VRisingServer.log"),
        ]

        def do_parse():
            import re
            log_path = None
            for p in log_candidates:
                if os.path.isfile(p):
                    log_path = p
                    break

            if not log_path:
                self.after(0, lambda: self.rcon_status_lbl.config(
                    text=f"Log not found. Checked: {log_candidates[0]}", fg=self.ACCENT))
                return

            # Show file size so user knows why it may take a moment
            try:
                fsize_mb = os.path.getsize(log_path) / (1024 * 1024)
                size_str = f"{fsize_mb:.1f} MB" if fsize_mb >= 1 else f"{int(fsize_mb*1024)} KB"
            except Exception:
                size_str = "?"

            self.after(0, lambda s=size_str: self.rcon_status_lbl.config(
                text=f"Reading log ({s})…", fg=self.YELLOW))

            # Pulse the status label while reading so user knows it's working
            _pulse_active = [True]
            _dots = [0]
            def _pulse():
                if not _pulse_active[0]:
                    return
                try:
                    _dots[0] = (_dots[0] + 1) % 4
                    dot_str = "." * _dots[0]
                    self.after(0, lambda d=dot_str, s=size_str: self.rcon_status_lbl.config(
                        text=f"Reading log ({s}){d}", fg=self.YELLOW))
                    self.after(600, _pulse)
                except RuntimeError:
                    pass  # window closed
            self.after(600, _pulse)

            try:
                t0 = time.time()
                with open(log_path, "r", encoding="utf-8-sig", errors="replace") as f:
                    content = f.read()
                elapsed = time.time() - t0
                _pulse_active[0] = False
                self.after(0, lambda s=size_str, e=elapsed: self.rcon_status_lbl.config(
                    text=f"Log read ({s} in {e:.1f}s) — scanning…", fg=self.YELLOW))
            except Exception as e:
                _pulse_active[0] = False
                self.after(0, lambda err=e: self.rcon_status_lbl.config(
                    text=f"Could not read log: {err}", fg=self.ACCENT))
                return

            # Only look at log entries after the last server start
            # Find the last occurrence of server startup marker
            start_markers = [i for i in range(len(content))
                             if content[i:].startswith("SteamPlatformSystem")]
            if start_markers:
                content = content[start_markers[-1]:]

            # Scan line-by-line in order so connect/disconnect sequence is preserved.
            # V Rising uses two different ID formats:
            #   Connect lines use the full 17-digit Steam ID (76561198061997676)
            #   Disconnect lines use a shorter session number (4276376706)
            # We build a map from session number -> steam ID on connect lines so
            # disconnect lines can be matched back to the right player.
            _re_id17     = re.compile(r'(\d{17})')           # full Steam ID
            _re_idany    = re.compile(r'\b(\d{7,17})\b')     # any numeric ID on the line
            _re_charname = re.compile(r'SteamId[:\s]+(\d{17})[,\s]+CharacterName[:\s]+([^\n\r,]+)', re.IGNORECASE)
            # Connect line: User '{Steam SESSIONID}' 'STEAMID64', ...
            _re_usercon  = re.compile(r"User '\{Steam (\d+)\}'[^']*'(\d{17})'", re.IGNORECASE)
            # Disconnect check first — "disconnected" contains "connected" as substring
            _re_dc  = re.compile(r'disconnected|connectionState_Closed|UnregisterUser', re.IGNORECASE)
            _re_con = re.compile(r"\bconnected\b", re.IGNORECASE)

            # session_to_steam: short session id -> full 17-digit steam id
            session_to_steam = {}
            # player_state: steam_id -> (name, is_connected)  — updated in log order
            player_state = {}

            for line in content.splitlines():
                # Try to extract connect line with both session id and steam id
                m_uc = _re_usercon.search(line)
                if m_uc:
                    session_id, steam_id = m_uc.group(1), m_uc.group(2)
                    session_to_steam[session_id] = steam_id
                    # Get character name if on same line
                    m_char = _re_charname.search(line)
                    name = m_char.group(2).strip() if m_char else f"{{Steam {session_id}}}"
                    if _re_dc.search(line):
                        player_state[steam_id] = (name, False)
                    else:
                        player_state[steam_id] = (name, True)
                    continue

                # Disconnect line — may only have the short session id
                if _re_dc.search(line):
                    # Try full steam id first
                    m17 = _re_id17.search(line)
                    if m17:
                        sid = m17.group(1)
                        name = player_state.get(sid, (sid,))[0]
                        player_state[sid] = (name, False)
                    else:
                        # Fall back to short session id -> look up steam id
                        for m in _re_idany.finditer(line):
                            short = m.group(1)
                            if short in session_to_steam:
                                sid = session_to_steam[short]
                                name = player_state.get(sid, (sid,))[0]
                                player_state[sid] = (name, False)
                    continue

                # Other connect/login lines with a full steam id
                m17 = _re_id17.search(line)
                if m17 and _re_con.search(line):
                    sid = m17.group(1)
                    m_char = _re_charname.search(line)
                    name = m_char.group(2).strip() if m_char else player_state.get(sid, (sid,))[0]
                    player_state[sid] = (name, True)

            final = {sid: name for sid, (name, connected) in player_state.items() if connected}

            try:
                self.after(0, lambda p=final, lp=log_path: self._show_players_from_log(p, lp))
            except RuntimeError:
                pass  # window was closed before scan finished

        threading.Thread(target=do_parse, daemon=True).start()

    def _show_players_from_log(self, players, log_path):
        """Display players parsed from the log file."""
        for w in self.player_list_frame.winfo_children():
            w.destroy()

        short_log = "…" + log_path[-40:] if len(log_path) > 43 else log_path
        if not players:
            tk.Label(self.player_list_frame,
                     text=f"No connected players found in log.\n({short_log})",
                     bg=self.PANEL_BG, fg=self.TEXT_DIM,
                     font=("Segoe UI", 8), justify="left").pack(padx=10, pady=8)
            self.rcon_status_lbl.config(text="Log parsed — 0 players", fg=self.TEXT_DIM)
            return

        self.rcon_status_lbl.config(
            text=f"Log parsed — {len(players)} player(s) found", fg=self.GREEN)

        hdr = tk.Frame(self.player_list_frame, bg=self.ACCENT2)
        hdr.pack(fill="x", pady=(0,2))
        tk.Label(hdr, text="Name", bg=self.ACCENT2, fg=self.TEXT,
                 font=("Segoe UI", 8, "bold"), width=22, anchor="w").pack(side="left", padx=6)
        tk.Label(hdr, text="Steam ID", bg=self.ACCENT2, fg=self.TEXT,
                 font=("Segoe UI", 8, "bold"), width=20, anchor="w").pack(side="left", padx=6)

        for steam_id, name in players.items():
            row = tk.Frame(self.player_list_frame, bg=self.PANEL_BG)
            row.pack(fill="x", pady=1)
            tk.Label(row, text=name, bg=self.PANEL_BG, fg=self.TEXT,
                     font=("Segoe UI", 9), width=22, anchor="w").pack(side="left", padx=6)
            tk.Label(row, text=steam_id, bg=self.PANEL_BG, fg=self.TEXT_DIM,
                     font=("Consolas", 8), width=20, anchor="w").pack(side="left", padx=6)
            tk.Button(row, text="+ Admin",
                      command=lambda sid=steam_id: self._add_to_adminlist(sid),
                      bg=self.ACCENT, fg="white", relief="flat",
                      font=("Segoe UI", 8), padx=6, pady=2, cursor="hand2").pack(side="left", padx=2)
            tk.Button(row, text="– Admin",
                      command=lambda sid=steam_id: self._remove_from_adminlist(sid),
                      bg="#7a3a00", fg="white", relief="flat",
                      font=("Segoe UI", 8), padx=6, pady=2, cursor="hand2").pack(side="left", padx=2)
            tk.Button(row, text="Kick",
                      command=lambda sid=steam_id: self._kick_player(sid),
                      bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                      font=("Segoe UI", 8), padx=6, pady=2, cursor="hand2").pack(side="left", padx=2)
            tk.Button(row, text="Ban",
                      command=lambda sid=steam_id: self._ban_player(sid),
                      bg="#5a0000", fg="white", relief="flat",
                      font=("Segoe UI", 8), padx=6, pady=2, cursor="hand2").pack(side="left", padx=2)
            tk.Button(row, text="Open Browser",
                      command=lambda sid=steam_id: self._open_steam_profile(sid),
                      bg="#1a3a5a", fg="white", relief="flat",
                      font=("Segoe UI", 8), padx=6, pady=2, cursor="hand2").pack(side="left", padx=2)

        # Info line about looking up Steam names
        tk.Label(self.player_list_frame,
                 text="Steam ID → display name: use the Open Browser button, or visit steamcommunity.com/profiles/{Steam ID}",
                 bg=self.PANEL_BG, fg=self.TEXT,
                 font=("Segoe UI", 8), justify="left").pack(anchor="w", padx=8, pady=(6,2))

    def _show_players(self, response, cmd_used=""):
        """Fallback — kept for RCON console use."""
        pass

    def _send_rcon_console(self):
        """Send a raw command via RCON and show the response in the console output box."""
        cmd = self.rcon_cmd_var.get().strip()
        if not cmd:
            return
        self.cfg["rcon_port"]     = self.rcon_port_var.get()
        self.cfg["rcon_password"] = self.rcon_password_var.get()
        self.rcon_cmd_var.set("")

        def _append(text):
            self.rcon_output.configure(state="normal")
            self.rcon_output.insert(tk.END, text)
            self.rcon_output.see(tk.END)
            self.rcon_output.configure(state="disabled")

        self.after(0, lambda: _append(f"\n> {cmd}\n"))

        def do_send():
            try:
                response = self._rcon_send(cmd)
                self.after(0, lambda r=response: _append(r + "\n"))
            except Exception as e:
                self.after(0, lambda err=e: _append(f"ERROR: {err}\n"))

        threading.Thread(target=do_send, daemon=True).start()

    def _player_query_failed(self, err):
        self.rcon_status_lbl.config(text=f"✗ {err}", fg=self.ACCENT)

    # ── Admin list file management ───────────────────────────────────────────
    def _get_adminlist_path(self):
        """
        Find the correct adminlist.txt location.
        V Rising checks several locations — we write to whichever already exists,
        or fall back to save-data/Settings which is the recommended persistent location.
        """
        base = self.cfg.get("server_path", "").strip()
        if not base:
            return None
        base = os.path.normpath(base)

        candidates = [
            # Persistent data path — recommended, survives server updates
            os.path.join(base, "save-data", "Settings", "adminlist.txt"),
            # AppData location
            os.path.expandvars(
                r"%USERPROFILE%\AppData\LocalLow\Stunlock Studios\VRisingServer\Settings\adminlist.txt"),
            # StreamingAssets — default template location, overwritten by updates
            os.path.join(base, "VRisingServer_Data", "StreamingAssets", "Settings", "adminlist.txt"),
        ]

        # Return the first one that already exists
        for path in candidates:
            if os.path.isfile(path):
                return path

        # None exist yet — return the preferred persistent location
        return candidates[0]

    def _load_adminlist(self):
        path = self._get_adminlist_path()
        if not path:
            messagebox.showerror("No Path", "Set the server path on the Server tab first.")
            return
        self.admin_text.delete("1.0", tk.END)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8-sig") as f:
                self.admin_text.insert("1.0", f.read())
            self.rcon_status_lbl.config(text=f"Loaded: {path}", fg=self.TEXT_DIM)
        else:
            self.rcon_status_lbl.config(
                text=f"Not found — will create at: {path}", fg=self.YELLOW)

    def _save_adminlist(self):
        path = self._get_adminlist_path()
        if not path:
            messagebox.showerror("No Path", "Set the server path on the Server tab first.")
            return
        os.makedirs(os.path.dirname(path), exist_ok=True)
        content = self.admin_text.get("1.0", tk.END).strip()
        with open(path, "w", encoding="utf-8") as f:
            f.write(content + "\n")

        # Also write to StreamingAssets as a fallback in case server reads from there
        base = os.path.normpath(self.cfg.get("server_path", "").strip())
        streaming_path = os.path.join(base, "VRisingServer_Data",
                                      "StreamingAssets", "Settings", "adminlist.txt")
        if os.path.isdir(os.path.dirname(streaming_path)) and streaming_path != path:
            try:
                with open(streaming_path, "w", encoding="utf-8") as f:
                    f.write(content + "\n")
            except Exception:
                pass

        messagebox.showinfo("Saved",
            f"adminlist.txt saved to:\n{path}\n\n"
            "Players need to run 'adminauth' in-game console to activate admin powers.\n\n"
            "Note: if you still lose admin on rejoin, check the ℹ How to activate admin\n"
            "button — adminauth must be typed each session.")

    def _show_admin_instructions(self):
        messagebox.showinfo("How to Activate Admin Powers",
            "After adding your Steam ID to adminlist.txt and saving:\n\n"
            "1. Make sure the server is running\n"
            "2. Join the server in-game\n"
            "3. Press F1 (or ~ ) to open the console\n"
            "4. Type:  adminauth\n"
            "5. Press Enter\n\n"
            "You should see a confirmation message.\n"
            "Admin powers are now active for your session.\n\n"
            "To deactivate:  type  admindeauth  in the console.\n\n"
            "⚠  By design, V Rising requires you to type adminauth\n"
            "every time you join the server — this is intentional\n"
            "and is not a bug. Your Steam ID staying in adminlist.txt\n"
            "just means you are ALLOWED to auth, not that you start\n"
            "with admin powers automatically.\n\n"
            "Think of adminlist.txt as a whitelist of who CAN become\n"
            "admin, and adminauth as actually activating it each session."
        )

    def _add_to_adminlist(self, steam_id):
        """Add a Steam ID to the admin text box if not already there."""
        current = self.admin_text.get("1.0", tk.END)
        if steam_id in current:
            messagebox.showinfo("Already Added", f"{steam_id} is already in the admin list.")
            return
        self.admin_text.insert(tk.END, steam_id + "\n")
        self.rcon_status_lbl.config(
            text=f"Added {steam_id} — click Save adminlist.txt to write to disk", fg=self.YELLOW)

    def _remove_from_adminlist(self, steam_id):
        """Remove a Steam ID from the admin text box."""
        current = self.admin_text.get("1.0", tk.END)
        if steam_id not in current:
            messagebox.showinfo("Not Found", f"{steam_id} is not in the admin list.")
            return
        lines = [l for l in current.splitlines() if l.strip() != steam_id]
        self.admin_text.delete("1.0", tk.END)
        self.admin_text.insert("1.0", "\n".join(lines).strip() + "\n")
        self.rcon_status_lbl.config(
            text=f"Removed {steam_id} — click Save adminlist.txt to write to disk", fg=self.YELLOW)

    def _kick_player(self, steam_id):
        """Kick a player via RCON."""
        if not messagebox.askyesno("Kick Player",
                f"Kick player with Steam ID:\n{steam_id}\n\nThey can reconnect immediately."):
            return
        def do_kick():
            try:
                self._rcon_send(f"kick {steam_id}")
                self.after(0, lambda: self.rcon_status_lbl.config(
                    text=f"Kicked {steam_id}", fg=self.GREEN))
            except Exception as e:
                self.after(0, lambda err=e: self.rcon_status_lbl.config(
                    text=f"Kick failed: {err}", fg=self.ACCENT))
        threading.Thread(target=do_kick, daemon=True).start()

    def _ban_player(self, steam_id):
        """Ban a player via RCON."""
        if not messagebox.askyesno("Ban Player",
                f"Ban player with Steam ID:\n{steam_id}\n\nThey will not be able to reconnect.\nYou can unban by editing the banlist manually."):
            return
        def do_ban():
            try:
                self._rcon_send(f"ban {steam_id}")
                self.after(0, lambda: self.rcon_status_lbl.config(
                    text=f"Banned {steam_id}", fg=self.GREEN))
            except Exception as e:
                self.after(0, lambda err=e: self.rcon_status_lbl.config(
                    text=f"Ban failed: {err}", fg=self.ACCENT))
        threading.Thread(target=do_ban, daemon=True).start()

    def _open_steam_profile(self, steam_id):
        """Open the player's Steam profile page in the default browser — user-initiated only."""
        import webbrowser
        url = f"https://steamcommunity.com/profiles/{steam_id}"
        if messagebox.askyesno("Open Browser",
                f"This will open your default web browser to:\n\n{url}\n\nOK to open?"):
            webbrowser.open(url)

    # ── Tab: Tools (Announce, Scheduled Restart, Backup) ────────────────────
    def _build_tab_tools(self):
        outer = self._scrollable_tab("  Tools  ")

        # ── Quick Announcements ──────────────────────────────────────────────
        self._section_plain(outer, 0, "Quick Announcements  (sent via RCON)")

        presets = [
            "Server restarting in 10 minutes - please find a safe spot!",
            "Server restarting in 5 minutes!",
            "Server restarting NOW - back in a few minutes.",
            "Welcome to the server!",
            "Server maintenance scheduled for tonight.",
        ]

        preset_frame = tk.Frame(outer, bg=self.PANEL_BG)
        preset_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(2,4))
        preset_frame.columnconfigure(0, weight=1)

        for i, msg in enumerate(presets):
            btn = tk.Button(preset_frame, text=msg,
                            command=lambda m=msg: self._send_announcement(m),
                            bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                            font=("Segoe UI", 8), padx=8, pady=3,
                            anchor="w", cursor="hand2")
            btn.grid(row=i, column=0, sticky="ew", pady=1)

        custom_row = tk.Frame(outer, bg=self.PANEL_BG)
        custom_row.grid(row=2, column=0, sticky="ew", padx=10, pady=(4,2))
        custom_row.columnconfigure(0, weight=1)
        self.announce_var = tk.StringVar()
        ttk.Entry(custom_row, textvariable=self.announce_var,
                  font=("Segoe UI", 9)).grid(row=0, column=0, sticky="ew", padx=(0,6))
        tk.Button(custom_row, text="Send", command=self._send_custom_announcement,
                  bg=self.ACCENT, fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=12, pady=3, cursor="hand2").grid(row=0, column=1)

        self.announce_status = tk.Label(outer, text="", bg=self.PANEL_BG,
                                         fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.announce_status.grid(row=3, column=0, sticky="w", padx=14, pady=(0,4))

        # ── Scheduled Restart ────────────────────────────────────────────────
        self._section_plain(outer, 4, "Scheduled Restart")

        tk.Label(outer, bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 8),
                 text="Warns players in-game before stopping the server.  "
                      "Save any game or server setting changes first — they take effect on the next start.").grid(
            row=5, column=0, sticky="w", padx=14, pady=(0, 4))

        sched_frame = tk.Frame(outer, bg=self.PANEL_BG)
        sched_frame.grid(row=6, column=0, sticky="ew", padx=10, pady=(2,4))

        tk.Label(sched_frame, text="Restart in:", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(0,6))

        self.restart_minutes_var = tk.IntVar(value=15)
        ttk.Spinbox(sched_frame, from_=1, to=1440,
                    textvariable=self.restart_minutes_var, width=6).pack(side="left")
        tk.Label(sched_frame, text="minutes", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(4,12))

        self.sched_start_btn = tk.Button(sched_frame, text="▶  Schedule",
                                          command=self._schedule_restart,
                                          bg=self.GREEN, fg="#0d1b2a", relief="flat",
                                          font=("Segoe UI", 9, "bold"), padx=10, pady=3,
                                          cursor="hand2")
        self.sched_start_btn.pack(side="left", padx=(0,6))

        self.sched_cancel_btn = tk.Button(sched_frame, text="✕  Cancel",
                                           command=self._cancel_scheduled_restart,
                                           bg=self.ACCENT, fg="white", relief="flat",
                                           font=("Segoe UI", 9, "bold"), padx=10, pady=3,
                                           state="disabled", cursor="hand2")
        self.sched_cancel_btn.pack(side="left")

        # Restart vs shutdown toggle
        self.sched_restart_var = tk.BooleanVar(value=True)
        tk.Checkbutton(sched_frame, text="Restart after shutdown",
                       variable=self.sched_restart_var,
                       bg=self.PANEL_BG, fg=self.TEXT, selectcolor=self.ENTRY_BG,
                       activebackground=self.PANEL_BG, activeforeground=self.TEXT,
                       font=("Segoe UI", 9), cursor="hand2").pack(side="left", padx=(14, 0))

        # Hint for the checkbox
        tk.Label(outer, bg=self.PANEL_BG, fg=self.TEXT_DIM, font=("Segoe UI", 8),
                 text="Uncheck 'Restart after shutdown' when you need time to install mods, "
                      "update server files, or perform maintenance before bringing the server back up.").grid(
            row=7, column=0, sticky="w", padx=14, pady=(0, 2))

        self.sched_status = tk.Label(outer, text="",
                                      bg=self.PANEL_BG, fg=self.TEXT_DIM,
                                      font=("Segoe UI", 8))
        self.sched_status.grid(row=8, column=0, sticky="w", padx=14, pady=(0,4))
        self.after(100, self._update_sched_idle_text)

        # ── Daily Automatic Restart ──────────────────────────────────────────
        self._section_plain(outer, 9, "Daily Automatic Restart")

        daily_frame = tk.Frame(outer, bg=self.PANEL_BG)
        daily_frame.grid(row=10, column=0, sticky="ew", padx=10, pady=(2,4))

        tk.Label(daily_frame, text="Restart time:", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(0,6))

        self.daily_hour_var = tk.IntVar(value=self.cfg.get("daily_restart_hour", 3))
        self.daily_minute_var = tk.IntVar(value=self.cfg.get("daily_restart_minute", 0))

        ttk.Spinbox(daily_frame, from_=0, to=23, textvariable=self.daily_hour_var,
                    width=4, format="%02.0f").pack(side="left")
        tk.Label(daily_frame, text=":", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Spinbox(daily_frame, from_=0, to=59, textvariable=self.daily_minute_var,
                    width=4, format="%02.0f").pack(side="left", padx=(0,12))

        tk.Label(daily_frame, text="Warn (min):", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(0,4))
        self.daily_warn_var = tk.IntVar(value=self.cfg.get("daily_restart_warn", 10))
        ttk.Spinbox(daily_frame, from_=1, to=60, textvariable=self.daily_warn_var,
                    width=4).pack(side="left", padx=(0,12))

        self.daily_enabled_var = tk.BooleanVar(value=self.cfg.get("daily_restart_enabled", False))
        self.daily_toggle_btn = tk.Button(daily_frame, text="Enable Daily Restart",
                                           command=self._toggle_daily_restart,
                                           bg=self.GREEN, fg="#0d1b2a", relief="flat",
                                           font=("Segoe UI", 9, "bold"), padx=10, pady=3,
                                           cursor="hand2")
        self.daily_toggle_btn.pack(side="left")

        self.daily_status = tk.Label(outer, text="Daily restart is disabled.",
                                      bg=self.PANEL_BG, fg=self.TEXT_DIM,
                                      font=("Segoe UI", 8))
        self.daily_status.grid(row=11, column=0, sticky="w", padx=14, pady=(0,2))

        self.daily_error_lbl = tk.Label(outer, text="",
                                         bg=self.PANEL_BG, fg=self.ACCENT,
                                         font=("Segoe UI", 8), wraplength=520, justify="left")
        self.daily_error_lbl.grid(row=12, column=0, sticky="w", padx=14, pady=(0,4))

        # Restore daily restart if it was enabled when manager last closed
        if self.cfg.get("daily_restart_enabled", False):
            self.after(1000, self._start_daily_restart_loop)

        # ── Backup Saves ─────────────────────────────────────────────────────
        self._section_plain(outer, 13, "Backup Save Data")

        backup_frame = tk.Frame(outer, bg=self.PANEL_BG)
        backup_frame.grid(row=14, column=0, sticky="ew", padx=10, pady=(2,4))

        tk.Label(backup_frame, text="Backup to:", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(0,6))

        default_backup = self.cfg.get("backup_dest") or os.path.join(
            os.path.expanduser("~"), "Desktop", "VRising_Backups")
        self.backup_dest_var = tk.StringVar(value=default_backup)
        # Save to config whenever it changes
        self.backup_dest_var.trace_add("write", lambda *_: self._save_backup_dest())
        ttk.Entry(backup_frame, textvariable=self.backup_dest_var, width=34).pack(side="left")
        tk.Button(backup_frame, text="Browse…",
                  command=self._browse_backup_dest,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, cursor="hand2").pack(side="left", padx=(4,0))

        btn_row = tk.Frame(outer, bg=self.PANEL_BG)
        btn_row.grid(row=15, column=0, sticky="ew", padx=10, pady=(4,2))
        tk.Button(btn_row, text="💾  Backup Now",
                  command=self._backup_now,
                  bg=self.GREEN, fg="#0d1b2a", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=14, pady=4, cursor="hand2").pack(side="left")

        self.backup_status = tk.Label(outer, text="", bg=self.PANEL_BG,
                                       fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.backup_status.grid(row=16, column=0, sticky="w", padx=14, pady=(0,4))

        backup_list_frame = tk.Frame(outer, bg=self.PANEL_BG)
        backup_list_frame.grid(row=17, column=0, sticky="ew", padx=10, pady=(2,8))
        backup_list_frame.columnconfigure(0, weight=1)
        self.backup_listbox = tk.Listbox(backup_list_frame, bg="#0d1b2a", fg=self.TEXT,
                                          font=("Consolas", 8), height=5,
                                          selectbackground=self.ACCENT2, relief="flat")
        self.backup_listbox.grid(row=0, column=0, sticky="ew")
        tk.Button(backup_list_frame, text="🗂  Open Backup Folder",
                  command=self._open_backup_folder,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, pady=2, cursor="hand2").grid(
            row=1, column=0, sticky="w", pady=(4,0))
        self._refresh_backup_list()

        # ── Scheduled Backup ─────────────────────────────────────────────────
        self._section_plain(outer, 18, "Scheduled Auto-Backup")

        sched_bk_frame = tk.Frame(outer, bg=self.PANEL_BG)
        sched_bk_frame.grid(row=19, column=0, sticky="ew", padx=10, pady=(2,4))

        tk.Label(sched_bk_frame, text="Every", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(0,6))
        self.backup_interval_var = tk.IntVar(value=self.cfg.get("backup_interval_hours", 6))
        ttk.Spinbox(sched_bk_frame, from_=1, to=168, textvariable=self.backup_interval_var,
                    width=4).pack(side="left")
        tk.Label(sched_bk_frame, text="hours    Keep last", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(6,6))
        self.backup_keep_var = tk.IntVar(value=self.cfg.get("backup_keep_count", 5))
        ttk.Spinbox(sched_bk_frame, from_=1, to=100, textvariable=self.backup_keep_var,
                    width=4).pack(side="left")
        tk.Label(sched_bk_frame, text="backups", bg=self.PANEL_BG,
                 fg=self.TEXT, font=("Segoe UI", 9)).pack(side="left", padx=(6,0))

        sched_bk_btn_row = tk.Frame(outer, bg=self.PANEL_BG)
        sched_bk_btn_row.grid(row=20, column=0, sticky="ew", padx=10, pady=(2,2))

        self.backup_sched_enabled = tk.BooleanVar(value=self.cfg.get("backup_sched_enabled", False))
        self.backup_sched_btn = tk.Button(
            sched_bk_btn_row,
            text="▶  Enable Auto-Backup" if not self.backup_sched_enabled.get() else "■  Disable Auto-Backup",
            command=self._toggle_backup_schedule,
            bg=self.GREEN if not self.backup_sched_enabled.get() else self.ACCENT,
            fg="#0d1b2a" if not self.backup_sched_enabled.get() else "white",
            relief="flat", font=("Segoe UI", 9, "bold"), padx=14, pady=4, cursor="hand2")
        self.backup_sched_btn.pack(side="left")

        self.backup_sched_status = tk.Label(outer, text="", bg=self.PANEL_BG,
                                             fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.backup_sched_status.grid(row=21, column=0, sticky="w", padx=14, pady=(0,6))

        # Restore schedule if it was enabled last session
        if self.backup_sched_enabled.get():
            self.after(2000, self._start_backup_schedule_loop)

        # ── Appearance / Theme ───────────────────────────────────────────────
        self._section_plain(outer, 22, "Appearance")

        theme_frame = tk.Frame(outer, bg=self.PANEL_BG)
        theme_frame.grid(row=23, column=0, sticky="ew", padx=10, pady=(2, 8))

        self.theme_var = tk.StringVar(value=self.cfg.get("theme", "Dark Blue (Default)"))
        col = 0
        for theme_name in THEMES:
            rb = tk.Radiobutton(
                theme_frame, text=theme_name,
                variable=self.theme_var, value=theme_name,
                command=self._on_theme_change,
                bg=self.PANEL_BG, fg=self.TEXT,
                selectcolor=self.ACCENT2,
                activebackground=self.PANEL_BG, activeforeground=self.TEXT,
                font=("Segoe UI", 9), cursor="hand2")
            rb.grid(row=0, column=col, sticky="w", padx=(0, 18))
            col += 1

    # ── Tab: Live Log Viewer ─────────────────────────────────────────────────
    def _build_tab_log(self):
        outer = ttk.Frame(self.notebook)
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(1, weight=1)
        self.notebook.add(outer, text="  Log  ")

        ctrl = tk.Frame(outer, bg=self.PANEL_BG, pady=4)
        ctrl.grid(row=0, column=0, sticky="ew", padx=10)

        tk.Button(ctrl, text="▶  Start Live Tail", command=self._start_log_tail,
                  bg=self.GREEN, fg="#0d1b2a", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=10, pady=3, cursor="hand2").pack(side="left", padx=(0,6))
        tk.Button(ctrl, text="■  Stop", command=self._stop_log_tail,
                  bg=self.ACCENT, fg="white", relief="flat",
                  font=("Segoe UI", 9, "bold"), padx=10, pady=3, cursor="hand2").pack(side="left", padx=(0,12))
        tk.Button(ctrl, text="Clear", command=self._clear_log,
                  bg=self.ACCENT2, fg=self.TEXT, relief="flat",
                  font=("Segoe UI", 8), padx=8, pady=3, cursor="hand2").pack(side="left")

        self.log_tail_status = tk.Label(ctrl, text="Stopped", bg=self.PANEL_BG,
                                         fg=self.TEXT_DIM, font=("Segoe UI", 8))
        self.log_tail_status.pack(side="left", padx=10)

        # Filter
        tk.Label(ctrl, text="Filter:", bg=self.PANEL_BG, fg=self.TEXT_DIM,
                 font=("Segoe UI", 8)).pack(side="right", padx=(0,4))
        self.log_filter_var = tk.StringVar()
        self.log_filter_var.trace_add("write", lambda *_: self._apply_log_filter())
        ttk.Entry(ctrl, textvariable=self.log_filter_var, width=16).pack(side="right")

        log_frame = tk.Frame(outer, bg="#0a1020")
        log_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(4,10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, bg="#0a1020", fg="#b0c4b0",
                                 insertbackground=self.GREEN, font=("Consolas", 8),
                                 relief="flat", wrap="none", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        vsb = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        vsb.grid(row=0, column=1, sticky="ns")
        hsb = ttk.Scrollbar(log_frame, orient="horizontal", command=self.log_text.xview)
        hsb.grid(row=1, column=0, sticky="ew")
        self.log_text.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        # Color tags for log levels
        self.log_text.tag_configure("error",   foreground="#ff6b6b")
        self.log_text.tag_configure("warn",    foreground="#f5a623")
        self.log_text.tag_configure("connect", foreground="#4ecca3")
        self.log_text.tag_configure("info",    foreground="#b0c4b0")

        self._log_tail_running = False
        self._log_lines_cache  = []   # all lines, for filter re-apply

    # ── Announcement methods ─────────────────────────────────────────────────
    def _send_announcement(self, msg):
        self.cfg["rcon_port"]     = self.rcon_port_var.get()
        self.cfg["rcon_password"] = self.rcon_password_var.get()
        def do():
            try:
                self._rcon_send(f"announce {msg}")
                self.after(0, lambda: self.announce_status.config(
                    text=f"✓ Sent: {msg[:60]}…" if len(msg)>60 else f"✓ Sent: {msg}",
                    fg=self.GREEN))
            except Exception as e:
                self.after(0, lambda err=e: self.announce_status.config(
                    text=f"✗ {err}", fg=self.ACCENT))
        threading.Thread(target=do, daemon=True).start()

    def _send_custom_announcement(self):
        msg = self.announce_var.get().strip()
        if msg:
            self._send_announcement(msg)
            self.announce_var.set("")

    # ── Scheduled restart ────────────────────────────────────────────────────
    def _schedule_restart(self):
        minutes = self.restart_minutes_var.get()
        do_restart = self.sched_restart_var.get()

        # Increment generation counter — any running countdown thread with an older
        # generation will see the mismatch and exit cleanly, preventing double-fires
        self._sched_generation = getattr(self, "_sched_generation", 0) + 1
        my_gen = self._sched_generation

        self._restart_cancel = False
        self.sched_start_btn.config(state="disabled")
        self.sched_cancel_btn.config(state="normal")
        self._restart_end_time = datetime.now() + timedelta(minutes=minutes)

        # Wording depends on whether we're restarting or just shutting down
        action_word   = "restarting" if do_restart else "shutting down for maintenance"
        action_now    = "restarting NOW!" if do_restart else "shutting down for maintenance NOW!"
        status_verb   = "Restarting" if do_restart else "Shutting down"
        bar_verb      = "Restart" if do_restart else "Shutdown"

        eta_str = self._restart_end_time.strftime("%H:%M")
        self.restart_countdown_lbl.config(
            text=f"⚠ {bar_verb} scheduled at {eta_str}", fg=self.YELLOW)

        def countdown(gen):
            all_warnings = {10: "10 minutes", 5: "5 minutes", 2: "2 minutes", 1: "1 minute"}
            warnings = {w_min: w_text for w_min, w_text in all_warnings.items()
                        if w_min < minutes}
            warned = set()
            while not self._restart_cancel and self._sched_generation == gen:
                remaining = (self._restart_end_time - datetime.now()).total_seconds()
                if remaining <= 0:
                    break
                status = f"{status_verb} in {int(remaining//60)}m {int(remaining%60)}s"
                self.after(0, lambda s=status: self.sched_status.config(text=s, fg=self.YELLOW))
                self.after(0, lambda s=status: self.restart_countdown_lbl.config(
                    text=f"⚠ {s}", fg=self.YELLOW))
                for w_min, w_text in warnings.items():
                    if w_min not in warned and remaining <= w_min * 60 + 2:
                        self._send_announcement(f"Server {action_word} in {w_text}!")
                        warned.add(w_min)
                time.sleep(1)

            # Only act if this is still the current generation and not cancelled
            if self._sched_generation == gen and not self._restart_cancel:
                self._send_announcement(f"Server {action_now}")
                self.after(0, lambda: self.restart_countdown_lbl.config(
                    text=f"⚠ {status_verb} NOW…", fg=self.ACCENT))
                time.sleep(3)
                if do_restart:
                    self.after(0, self._do_restart)
                else:
                    self.after(0, self._stop_server)
                    self.after(0, lambda: self.restart_countdown_lbl.config(text=""))
                    self.after(0, self._update_sched_idle_text)
            else:
                self.after(0, self._update_sched_idle_text)
                self.after(0, lambda: self.restart_countdown_lbl.config(text=""))
            self.after(0, lambda: self.sched_start_btn.config(state="normal"))
            self.after(0, lambda: self.sched_cancel_btn.config(state="disabled"))

        threading.Thread(target=countdown, args=(my_gen,), daemon=True).start()

    def _cancel_scheduled_restart(self):
        self._restart_cancel = True

    def _update_sched_idle_text(self):
        """Set the scheduled-restart status label and status bar daily indicator."""
        try:
            if self.daily_enabled_var.get():
                h = self.daily_hour_var.get()
                m = self.daily_minute_var.get()
                self.sched_status.config(
                    text=f"No one-time restart scheduled.  (Daily auto-restart at {h:02d}:{m:02d} is active)",
                    fg=self.TEXT_DIM)
                self.daily_restart_status_lbl.config(
                    text=f"⏰ Daily restart {h:02d}:{m:02d}", fg=self.TEXT)
            else:
                self.sched_status.config(text="No restart scheduled.", fg=self.TEXT_DIM)
                self.daily_restart_status_lbl.config(text="")
        except AttributeError:
            pass  # widgets not ready yet

    def _do_restart(self):
        self._stop_server()
        time.sleep(2)
        self._start_server()
        self.sched_status.config(text="Server restarted ✓", fg=self.GREEN)
        self.restart_countdown_lbl.config(text="")
        self.after(4000, self._update_sched_idle_text)

    # ── Daily Restart methods ────────────────────────────────────────────────
    def _toggle_daily_restart(self):
        if self.daily_enabled_var.get():
            self.daily_enabled_var.set(False)
            self._daily_restart_cancel = True
            self.daily_toggle_btn.config(text="Enable Daily Restart", bg=self.GREEN, fg="#0d1b2a")
            self.daily_status.config(text="Daily restart is disabled.", fg=self.TEXT_DIM)
            self.cfg["daily_restart_enabled"] = False
            self.cfg["daily_restart_hour"]    = self.daily_hour_var.get()
            self.cfg["daily_restart_minute"]  = self.daily_minute_var.get()
            self.cfg["daily_restart_warn"]    = self.daily_warn_var.get()
            save_config(self.cfg)
        else:
            self._start_daily_restart_loop()
        self._update_sched_idle_text()

    def _start_daily_restart_loop(self):
        self.daily_enabled_var.set(True)
        self._daily_restart_cancel = False
        h = self.daily_hour_var.get()
        m = self.daily_minute_var.get()
        self.daily_toggle_btn.config(text="Disable Daily Restart", bg=self.ACCENT, fg="white")
        self.daily_status.config(
            text=f"Daily restart enabled — will restart at {h:02d}:{m:02d} every night.",
            fg=self.GREEN)
        self.cfg["daily_restart_enabled"] = True
        self.cfg["daily_restart_hour"]    = h
        self.cfg["daily_restart_minute"]  = m
        self.cfg["daily_restart_warn"]    = self.daily_warn_var.get()
        save_config(self.cfg)
        t = threading.Thread(target=self._daily_restart_loop, daemon=True)
        t.start()

    def _daily_restart_loop(self):
        """Background thread: waits until scheduled time, warns, restarts. Loops nightly."""
        import datetime
        while not getattr(self, "_daily_restart_cancel", False):
            try:
                h = self.cfg.get("daily_restart_hour", 3)
                m = self.cfg.get("daily_restart_minute", 0)
                warn_minutes = self.cfg.get("daily_restart_warn", 10)
            except Exception as e:
                self.after(0, lambda err=e: self.daily_status.config(
                    text=f"Daily restart config error: {err}", fg=self.ACCENT))
                time.sleep(60)
                continue

            try:
                now = datetime.datetime.now()
                target = now.replace(hour=h, minute=m, second=0, microsecond=0)
                if target <= now:
                    target += datetime.timedelta(days=1)

                def _update_status_until(tgt):
                    if getattr(self, "_daily_restart_cancel", False):
                        return
                    remaining = tgt - datetime.datetime.now()
                    total_secs = int(remaining.total_seconds())
                    if total_secs <= 0:
                        return
                    hrs, rem = divmod(total_secs, 3600)
                    mins, secs = divmod(rem, 60)
                    if hrs > 0:
                        countdown = f"{hrs}h {mins}m"
                    else:
                        countdown = f"{mins}m {secs}s"
                    self.after(0, lambda: self.daily_status.config(
                        text=f"Daily restart at {tgt.hour:02d}:{tgt.minute:02d} — next in {countdown}",
                        fg=self.GREEN))
                    self.after(10000, lambda: _update_status_until(tgt))

                self.after(0, lambda tgt=target: _update_status_until(tgt))

                # Sleep until warn_minutes before restart
                warn_start = target - datetime.timedelta(minutes=warn_minutes)
                while not getattr(self, "_daily_restart_cancel", False):
                    remaining = (warn_start - datetime.datetime.now()).total_seconds()
                    if remaining <= 0:
                        break
                    time.sleep(min(30, max(1, remaining)))

                if getattr(self, "_daily_restart_cancel", False):
                    break

                # Warning phase
                warned_at = set()
                warning_minutes = sorted(set(
                    [w for w in [warn_minutes, 5, 2, 1] if w <= warn_minutes]
                ), reverse=True)

                self.after(0, lambda wl=warning_minutes: self.daily_status.config(
                    text=f"Warning phase started — will warn at: {wl} min", fg=self.YELLOW))

                # Fire the first applicable warning immediately on entry (don't wait for the loop)
                remaining_now = (target - datetime.datetime.now()).total_seconds() / 60.0
                for wm in warning_minutes:
                    if remaining_now <= wm + 0.5 and wm not in warned_at:
                        warned_at.add(wm)
                        msg = f"Server restarting in {wm} minute{'s' if wm != 1 else ''}! Please find a safe spot."
                        self._send_rcon_silent(f"announce {msg}")
                        break  # only send the most relevant one immediately

                while not getattr(self, "_daily_restart_cancel", False):
                    remaining_secs = (target - datetime.datetime.now()).total_seconds()
                    remaining_mins = remaining_secs / 60.0
                    for wm in warning_minutes:
                        if remaining_mins <= wm + 0.2 and wm not in warned_at:
                            warned_at.add(wm)
                            msg = f"Server restarting in {wm} minute{'s' if wm != 1 else ''}! Please find a safe spot."
                            self._send_rcon_silent(f"announce {msg}")
                    if remaining_secs <= 5:
                        break
                    time.sleep(5)

                if getattr(self, "_daily_restart_cancel", False):
                    break

                # Do the restart — only if server is actually running
                if not self.server_process and not self._find_server_process():
                    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    self._write_restart_log(f"SKIPPED at {ts} — server was not running at restart time")
                    self.after(0, lambda: self.daily_status.config(
                        text="Daily restart skipped — server was not running.", fg=self.YELLOW))
                    time.sleep(90)
                    continue

                self.after(0, lambda: self.daily_status.config(
                    text="Daily restart running...", fg=self.TEXT_DIM))
                self._send_rcon_silent("announcerestart")
                time.sleep(3)
                self._stop_server()
                time.sleep(5)
                self._start_server()
                restart_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self._write_restart_log(f"SUCCESS — daily restart completed at {restart_time}")
                self.after(0, lambda rt=restart_time: self.daily_status.config(
                    text=f"Last daily restart completed at {rt}. Next at {h:02d}:{m:02d}.",
                    fg=self.GREEN))

                # Sleep past the restart time before looping to avoid double-trigger
                time.sleep(90)

            except Exception as e:
                import traceback
                err_text = f"Loop error: {e}"
                full_err = traceback.format_exc()
                print(f"[VRising Manager] Daily restart loop exception:\n{full_err}")
                ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                self._write_restart_log(f"ERROR at {ts} — {e}\n{full_err}")
                self.after(0, lambda t=err_text: self.daily_status.config(
                    text=t, fg=self.ACCENT))
                self.after(0, lambda t=err_text: self.daily_error_lbl.config(text=t))
                time.sleep(60)
                continue

    def _send_rcon_silent(self, command):
        """Send an RCON command silently — used by automated restarts. Logs failures to daily status."""
        try:
            self._rcon_send(command)
        except Exception as e:
            err_text = f"RCON ERR ({command[:30]}): {e}"
            print(f"[VRising Manager] RCON failed for '{command[:40]}': {e}")
            self.after(0, lambda t=err_text: self.daily_status.config(
                text=t, fg=self.ACCENT))
            self.after(0, lambda t=err_text: self.daily_error_lbl.config(text=t))

    def _write_restart_log(self, message):
        """Append a timestamped entry to vrising_restart_log.txt next to the manager script."""
        try:
            log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vrising_restart_log.txt")
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"[VRising Manager] Could not write restart log: {e}")

    # ── Backup methods ───────────────────────────────────────────────────────
    def _browse_backup_dest(self):
        folder = filedialog.askdirectory(title="Select backup destination folder")
        if folder:
            self.backup_dest_var.set(os.path.normpath(folder))

    def _save_backup_dest(self):
        """Persist backup destination to config whenever it changes."""
        try:
            self.cfg["backup_dest"] = self.backup_dest_var.get().strip()
            save_config(self.cfg)
        except Exception:
            pass

    def _backup_now(self):
        base = os.path.normpath(self.path_var.get().strip())
        src  = os.path.join(base, "save-data")
        if not os.path.isdir(src):
            messagebox.showerror("Not Found", f"save-data folder not found at:\n{src}")
            return
        dest_root = os.path.normpath(self.backup_dest_var.get().strip())
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest = os.path.join(dest_root, f"VRising_backup_{timestamp}")
        self.backup_status.config(text="Backing up…", fg=self.YELLOW)
        self.update_idletasks()

        def do_backup():
            try:
                shutil.copytree(src, dest)
                size_mb = sum(
                    os.path.getsize(os.path.join(dp, f))
                    for dp, _, files in os.walk(dest) for f in files
                ) / (1024 * 1024)
                self._prune_old_backups(dest_root)
                msg = f"✓ Backup complete — {size_mb:.1f} MB → {dest}"
                self.after(0, lambda: self.backup_status.config(text=msg, fg=self.GREEN))
                self.after(0, self._refresh_backup_list)
            except Exception as e:
                self.after(0, lambda err=e: self.backup_status.config(
                    text=f"✗ Backup failed: {err}", fg=self.ACCENT))

        threading.Thread(target=do_backup, daemon=True).start()

    def _refresh_backup_list(self):
        if not hasattr(self, "backup_listbox"):
            return
        dest_root = self.backup_dest_var.get().strip()
        self.backup_listbox.delete(0, tk.END)
        if os.path.isdir(dest_root):
            folders = sorted(
                [f for f in os.listdir(dest_root) if f.startswith("VRising_backup_")],
                reverse=True)
            for f in folders:
                self.backup_listbox.insert(tk.END, f)
        if self.backup_listbox.size() == 0:
            self.backup_listbox.insert(tk.END, "(no backups yet)")

    def _open_backup_folder(self):
        dest = self.backup_dest_var.get().strip()
        os.makedirs(dest, exist_ok=True)
        os.startfile(dest)

    # ── Theme switching ──────────────────────────────────────────────────────
    def _on_theme_change(self):
        """Apply the selected theme immediately and save it to config."""
        name = self.theme_var.get()
        t = THEMES.get(name, THEMES["Dark Blue (Default)"])
        self.DARK_BG    = t["DARK_BG"]
        self.PANEL_BG   = t["PANEL_BG"]
        self.ACCENT     = t["ACCENT"]
        self.ACCENT2    = t["ACCENT2"]
        self.TEXT       = t["TEXT"]
        self.TEXT_DIM   = t["TEXT_DIM"]
        self.GREEN      = t["GREEN"]
        self.YELLOW     = t["YELLOW"]
        self.ENTRY_BG   = t["ENTRY_BG"]
        self.SLIDER_TRG = self.ACCENT

        self._apply_ttk_styles()
        self.configure(bg=self.DARK_BG)

        # Walk every tk widget and update bg/fg where they match any old theme color
        self._recolor_widgets(self)

        self.cfg["theme"] = name
        save_config(self.cfg)

        messagebox.showinfo("Theme Applied",
            f"Theme \"{name}\" applied.\n\n"
            "Most colors update instantly. If anything looks off, "
            "restart the manager to see the full effect.")

    def _recolor_widgets(self, widget):
        """Recursively update bg/fg on all tk (non-ttk) widgets."""
        all_bg = {v["DARK_BG"] for v in THEMES.values()} | \
                 {v["PANEL_BG"] for v in THEMES.values()} | \
                 {v["ACCENT2"] for v in THEMES.values()} | \
                 {v["ENTRY_BG"] for v in THEMES.values()}
        all_fg = {v["TEXT"] for v in THEMES.values()} | \
                 {v["TEXT_DIM"] for v in THEMES.values()} | \
                 {v["GREEN"] for v in THEMES.values()} | \
                 {v["YELLOW"] for v in THEMES.values()} | \
                 {v["ACCENT"] for v in THEMES.values()}

        # Mapping: old bg -> new bg
        bg_map = {
            **{v["DARK_BG"]:  self.DARK_BG  for v in THEMES.values()},
            **{v["PANEL_BG"]: self.PANEL_BG for v in THEMES.values()},
            **{v["ACCENT2"]:  self.ACCENT2  for v in THEMES.values()},
            **{v["ENTRY_BG"]: self.ENTRY_BG for v in THEMES.values()},
        }
        fg_map = {
            **{v["TEXT"]:     self.TEXT     for v in THEMES.values()},
            **{v["TEXT_DIM"]: self.TEXT_DIM for v in THEMES.values()},
            **{v["GREEN"]:    self.GREEN    for v in THEMES.values()},
            **{v["YELLOW"]:   self.YELLOW   for v in THEMES.values()},
            **{v["ACCENT"]:   self.ACCENT   for v in THEMES.values()},
        }

        def walk(w):
            try:
                cur_bg = w.cget("bg")
                if cur_bg in bg_map:
                    w.configure(bg=bg_map[cur_bg])
            except tk.TclError:
                pass
            try:
                cur_fg = w.cget("fg")
                if cur_fg in fg_map:
                    w.configure(fg=fg_map[cur_fg])
            except tk.TclError:
                pass
            try:
                cur_sel = w.cget("selectcolor")
                if cur_sel in bg_map:
                    w.configure(selectcolor=bg_map[cur_sel])
            except tk.TclError:
                pass
            for child in w.winfo_children():
                walk(child)

        walk(widget)

    def _prune_old_backups(self, dest_root):
        """Delete oldest VRising_backup_* folders beyond the keep count."""
        keep = max(1, self.backup_keep_var.get())
        if not os.path.isdir(dest_root):
            return
        folders = sorted(
            [f for f in os.listdir(dest_root) if f.startswith("VRising_backup_")],
            reverse=True)   # newest first
        for old in folders[keep:]:
            old_path = os.path.join(dest_root, old)
            try:
                shutil.rmtree(old_path)
            except Exception:
                pass

    def _toggle_backup_schedule(self):
        """Enable or disable the auto-backup schedule and persist the choice."""
        enabled = not self.backup_sched_enabled.get()
        self.backup_sched_enabled.set(enabled)
        self.cfg["backup_sched_enabled"]    = enabled
        self.cfg["backup_interval_hours"]   = self.backup_interval_var.get()
        self.cfg["backup_keep_count"]       = self.backup_keep_var.get()
        save_config(self.cfg)
        if enabled:
            self.backup_sched_btn.config(
                text="■  Disable Auto-Backup", bg=self.ACCENT, fg="white")
            self._start_backup_schedule_loop()
        else:
            self.backup_sched_btn.config(
                text="▶  Enable Auto-Backup", bg=self.GREEN, fg="#0d1b2a")
            self.backup_sched_status.config(
                text="Auto-backup disabled.", fg=self.TEXT_DIM)

    def _start_backup_schedule_loop(self):
        """Kick off the background loop that fires a backup every N hours."""
        interval_hours = max(1, self.backup_interval_var.get())
        self._backup_sched_next = datetime.now() + timedelta(hours=interval_hours)
        self._backup_schedule_tick()

    def _backup_schedule_tick(self):
        """Called every 60 s; fires a backup when the scheduled time arrives."""
        if not self.backup_sched_enabled.get():
            return  # schedule was disabled — stop ticking
        now = datetime.now()
        remaining = self._backup_sched_next - now
        total_sec = max(0, int(remaining.total_seconds()))
        hrs, rem  = divmod(total_sec, 3600)
        mins      = rem // 60
        try:
            self.backup_sched_status.config(
                text=f"Next auto-backup in {hrs}h {mins:02d}m", fg=self.TEXT_DIM)
        except RuntimeError:
            return  # window closed

        if now >= self._backup_sched_next:
            # Time to back up — reset timer first, then run backup
            interval_hours = max(1, self.backup_interval_var.get())
            self._backup_sched_next = now + timedelta(hours=interval_hours)
            self._run_scheduled_backup()

        # Re-schedule this tick in 60 s
        try:
            self.after(60_000, self._backup_schedule_tick)
        except RuntimeError:
            pass  # window closed

    def _run_scheduled_backup(self):
        """Perform a backup triggered by the schedule (silent, no popup on errors)."""
        base = os.path.normpath(self.path_var.get().strip())
        src  = os.path.join(base, "save-data")
        if not os.path.isdir(src):
            return
        dest_root = os.path.normpath(self.backup_dest_var.get().strip())
        if not dest_root:
            return
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        dest = os.path.join(dest_root, f"VRising_backup_{timestamp}")

        def do_backup():
            try:
                shutil.copytree(src, dest)
                self._prune_old_backups(dest_root)
                msg = f"Auto-backup at {timestamp} ✓"
                try:
                    self.after(0, lambda: self.backup_sched_status.config(
                        text=msg, fg=self.GREEN))
                    self.after(0, self._refresh_backup_list)
                except RuntimeError:
                    pass
            except Exception:
                pass  # silent on scheduled errors

        threading.Thread(target=do_backup, daemon=True).start()

    # ── Log tail methods ─────────────────────────────────────────────────────
    def _get_log_path(self):
        base = os.path.normpath(self.path_var.get().strip())
        candidates = [
            os.path.join(base, "logs", "VRisingServer.log"),
            os.path.join(base, "VRisingServer_Data", "logs", "VRisingServer.log"),
            os.path.expandvars(
                r"%USERPROFILE%\AppData\LocalLow\Stunlock Studios\VRisingServer\VRisingServer.log"),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return candidates[0]   # return first as default even if not found yet

    def _start_log_tail(self):
        if self._log_tail_running:
            return
        self._log_tail_running = True
        self.log_tail_status.config(text="● Live", fg=self.GREEN)
        threading.Thread(target=self._tail_loop, daemon=True).start()

    def _stop_log_tail(self):
        self._log_tail_running = False
        self.log_tail_status.config(text="Stopped", fg=self.TEXT_DIM)

    def _clear_log(self):
        self._log_lines_cache = []
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def _tail_loop(self):
        log_path = self._get_log_path()
        # Seek to end first so we only show new lines (unless file is small)
        try:
            size = os.path.getsize(log_path)
            seek_pos = max(0, size - 8192)   # show last ~8 KB on start
        except Exception:
            seek_pos = 0

        while self._log_tail_running:
            try:
                with open(log_path, "r", encoding="utf-8-sig", errors="replace") as f:
                    f.seek(seek_pos)
                    while self._log_tail_running:
                        line = f.readline()
                        if line:
                            seek_pos = f.tell()
                            self.after(0, lambda l=line.rstrip(): self._append_log_line(l))
                        else:
                            time.sleep(0.5)
            except FileNotFoundError:
                self.after(0, lambda: self.log_tail_status.config(
                    text=f"Waiting for log: {os.path.basename(log_path)}", fg=self.YELLOW))
                time.sleep(3)
            except Exception as e:
                self.after(0, lambda err=e: self.log_tail_status.config(
                    text=f"Log error: {err}", fg=self.ACCENT))
                time.sleep(3)

    def _append_log_line(self, line):
        self._log_lines_cache.append(line)
        # Keep cache from growing unbounded
        if len(self._log_lines_cache) > 5000:
            self._log_lines_cache = self._log_lines_cache[-4000:]

        filt = self.log_filter_var.get().lower() if hasattr(self, "log_filter_var") else ""
        if filt and filt not in line.lower():
            return

        tag = "info"
        ll = line.lower()
        if "error" in ll or "exception" in ll or "fatal" in ll:
            tag = "error"
        elif "warn" in ll:
            tag = "warn"
        elif "connect" in ll or "disconnect" in ll or "login" in ll:
            tag = "connect"

        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, line + "\n", tag)
        # Auto-scroll only if already at bottom
        if self.log_text.yview()[1] > 0.95:
            self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _apply_log_filter(self):
        filt = self.log_filter_var.get().lower()
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        for line in self._log_lines_cache:
            if not filt or filt in line.lower():
                tag = "info"
                ll = line.lower()
                if "error" in ll or "exception" in ll: tag = "error"
                elif "warn" in ll: tag = "warn"
                elif "connect" in ll or "disconnect" in ll: tag = "connect"
                self.log_text.insert(tk.END, line + "\n", tag)
        self.log_text.configure(state="disabled")

    # ── Find the active settings directory ──────────────────────────────────
    def _find_settings_dirs(self):
        """
        Return a list of candidate Settings folders in priority order.
        """
        candidates = []
        raw = self.cfg.get("server_path", "").strip()
        base = os.path.normpath(raw) if raw else ""
        if base:
            candidates.append(os.path.join(base, "save-data", "Settings"))
            candidates.append(os.path.join(base, "VRisingServer_Data",
                                            "StreamingAssets", "Settings"))
        appdata = os.path.expandvars(
            r"%USERPROFILE%\AppData\LocalLow\Stunlock Studios\VRisingServer\Settings")
        candidates.append(appdata)
        return candidates

    # ── Import existing server JSON values into the UI ───────────────────────
    def _import_from_server_files(self):
        """
        Searches all known Settings locations, reads the first JSON files
        it finds, and pushes their values into the sliders/fields.
        Returns (found_list, checked_list) so callers can report results.
        """
        raw = self.cfg.get("server_path", "").strip()
        checked = self._find_settings_dirs()
        if not raw:
            return [], checked

        # Find which directory actually has the files
        host_path = None
        game_path = None
        for d in checked:
            h = os.path.join(d, "ServerHostSettings.json")
            g = os.path.join(d, "ServerGameSettings.json")
            if host_path is None and os.path.isfile(h):
                host_path = h
            if game_path is None and os.path.isfile(g):
                game_path = g
            if host_path and game_path:
                break

        found_msg = []

        # ── Pull from ServerHostSettings.json ────────────────────────────────
        if host_path:
            host = self._read_json_safe(host_path)
            if host:
                found_msg.append(f"Host: {host_path}")
                if "Name"               in host: self.server_name_var.set(host["Name"])
                if "Description"        in host: self.description_var.set(host["Description"])
                if "Password"           in host: self.password_var.set(host["Password"])
                if "SaveName"           in host: self.save_name_var.set(host["SaveName"])
                if "Port"               in host: self.game_port_var.set(host["Port"])
                if "QueryPort"          in host: self.query_port_var.set(host["QueryPort"])
                if "MaxConnectedUsers"  in host: self.max_players_var.set(host["MaxConnectedUsers"])
                if "MaxConnectedAdmins" in host: self.max_admins_var.set(host["MaxConnectedAdmins"])
                if "ServerFps"          in host: self.server_fps_var.set(host["ServerFps"])
                if "AutoSaveInterval"   in host: self.autosave_var.set(host["AutoSaveInterval"])
                if "AutoSaveCount"      in host: self.autosave_count_var.set(host["AutoSaveCount"])
                if "CompressSaveFiles"  in host: self.compress_saves_var.set(host["CompressSaveFiles"])
                if "ListOnSteam"        in host: self.list_steam_var.set(host["ListOnSteam"])
                if "ListOnEOS"          in host: self.list_eos_var.set(host["ListOnEOS"])
                if "Secure"             in host: self.secure_var.set(host["Secure"])
                if "GameSettingsPreset" in host: self.preset_var.set(host["GameSettingsPreset"])
                if "Rcon" in host:
                    rcon = host["Rcon"]
                    if "Enabled"  in rcon: self.rcon_enabled_var.set(rcon["Enabled"])
                    if "Port"     in rcon: self.rcon_port_var.set(rcon["Port"])
                    if "Password" in rcon: self.rcon_password_var.set(rcon["Password"])

        # ── Pull from ServerGameSettings.json ────────────────────────────────
        if game_path:
            game = self._read_json_safe(game_path)
            if game:
                found_msg.append(f"Game: {game_path}")
                # Nested GameTimeModifiers
                gtm = game.get("GameTimeModifiers", {})
                if "DayDurationInSeconds"   in gtm:
                    self.cycle_entry_var.set(str(int(gtm["DayDurationInSeconds"] / 60)))
                if "DayStartHour"           in gtm: self.day_start_var.set(gtm["DayStartHour"])
                if "DayEndHour"             in gtm: self.day_end_var.set(gtm["DayEndHour"])
                if "BloodMoonFrequency_Min" in gtm: self.bm_freq_min_var.set(gtm["BloodMoonFrequency_Min"])
                if "BloodMoonFrequency_Max" in gtm: self.bm_freq_max_var.set(gtm["BloodMoonFrequency_Max"])
                if "BloodMoonBuff"          in gtm: self.bm_dur_var.set(gtm["BloodMoonBuff"])

                # Top-level fields
                if "CastleDecayRateModifier"         in game: self.decay_var.set(game["CastleDecayRateModifier"])
                if "CastleBloodEssenceDrainModifier" in game: self.drain_var.set(game["CastleBloodEssenceDrainModifier"])
                if "PlayerXPRate"                    in game: self.xp_var.set(game["PlayerXPRate"])
                if "DropTableModifier_General"       in game: self.drop_var.set(game["DropTableModifier_General"])
                if "MaterialYieldModifier_Global"    in game: self.resource_var.set(game["MaterialYieldModifier_Global"])
                if "SoulShardModifier"               in game: self.shard_var.set(game["SoulShardModifier"])
                if "BloodEssenceYieldModifier"       in game: self.blood_essence_yield_var.set(game["BloodEssenceYieldModifier"])
                if "InventoryStacksModifier"         in game: self.inventory_stacks_var.set(game["InventoryStacksModifier"])
                if "BuildCostModifier"               in game: self.build_cost_var.set(game["BuildCostModifier"])
                if "CraftRateModifier"               in game: self.craft_rate_var.set(game["CraftRateModifier"])
                if "RecipeCostModifier"              in game: self.recipe_cost_var.set(game["RecipeCostModifier"])
                if "ResearchCostModifier"            in game: self.research_cost_var.set(game["ResearchCostModifier"])
                if "ResearchTimeModifier"            in game: self.research_time_var.set(game["ResearchTimeModifier"])
                if "RefinementCostModifier"          in game: self.refine_cost_var.set(game["RefinementCostModifier"])
                if "RefinementRateModifier"          in game: self.refine_rate_var.set(game["RefinementRateModifier"])
                if "DismantleResourceModifier"       in game: self.dismantle_var.set(game["DismantleResourceModifier"])
                if "RepairCostModifier"              in game: self.repair_cost_var.set(game["RepairCostModifier"])
                if "ServantConvertRateModifier"      in game: self.servant_var.set(game["ServantConvertRateModifier"])
                if "PlayerStartingBloodEssence"      in game: self.blood_start_var.set(game["PlayerStartingBloodEssence"])
                if "GameModeType"                    in game: self.pvp_var.set(game["GameModeType"] == "PvP")
                if "AutoSaveInterval"                in game: self.autosave_var.set(game["AutoSaveInterval"])
                if "TeleportBoundItems"              in game: self.teleport_bound_var.set(game["TeleportBoundItems"])
                if "BloodBoundEquipment"             in game: self.blood_bound_var.set(game["BloodBoundEquipment"])
                if "BatBoundItems"                   in game: self.bat_bound_var.set(game["BatBoundItems"])
                if "CanLootEnemyContainers"          in game: self.loot_containers_var.set(game["CanLootEnemyContainers"])
                if "AllowGlobalChat"                 in game: self.global_chat_var.set(game["AllowGlobalChat"])
                if "AllWaypointsUnlocked"            in game: self.all_waypoints_var.set(game["AllWaypointsUnlocked"])
                if "ClanSize"                        in game: self.clan_size_var.set(game["ClanSize"])
                if "CastleRelocationEnabled"         in game: self.castle_reloc_var.set(game["CastleRelocationEnabled"])
                if "CastleRelocationCooldown"        in game: self.castle_reloc_cooldown_var.set(int(game["CastleRelocationCooldown"]))
                if "CastleMinimumDistanceInFloors"   in game: self.castle_min_dist_var.set(game["CastleMinimumDistanceInFloors"])
                if "FreeCastleClaim"                 in game: self.free_castle_claim_var.set(game["FreeCastleClaim"])
                if "FreeCastleRaid"                  in game: self.free_castle_raid_var.set(game["FreeCastleRaid"])
                if "FreeCastleDestroy"               in game: self.free_castle_dest_var.set(game["FreeCastleDestroy"])
                if "InactivityKillEnabled"           in game: self.inactivity_kill_var.set(game["InactivityKillEnabled"])
                if "DisableDisconnectedDeadEnabled"  in game: self.disconnected_dead_var.set(game["DisableDisconnectedDeadEnabled"])
                if "DisableDisconnectedDeadTimer"    in game: self.disconnected_dead_timer_var.set(game["DisableDisconnectedDeadTimer"])
                if "DisconnectedSunImmunityTime"     in game: self.disconnect_sun_var.set(int(game["DisconnectedSunImmunityTime"]))
                if "StartingProgressionLevel"        in game: self.starting_level_var.set(game["StartingProgressionLevel"])
                if "PvPProtectionMode"               in game: self.pvp_protection_var.set(game["PvPProtectionMode"])
                if "DeathContainerPermission"        in game: self.death_container_var.set(game["DeathContainerPermission"])
                if "InventoryDropOnDeath"            in game: self.inventory_drop_var.set(game["InventoryDropOnDeath"])
                if "SiegeWeaponHealth"               in game: self.siege_weapon_health_var.set(game["SiegeWeaponHealth"])
                if "AnnounceSiegeWeaponSpawn"        in game: self.announce_siege_var.set(game["AnnounceSiegeWeaponSpawn"])
                if "ShowSiegeWeaponMapIcon"          in game: self.show_siege_icon_var.set(game["ShowSiegeWeaponMapIcon"])
                if "RelicSpawnType"                  in game: self.relic_spawn_var.set(game["RelicSpawnType"])
                pi = game.get("PlayerInteractionSettings", {})
                if "VSPlayerWeekdayTime" in pi:
                    self.pvp_player_wday_start.set(pi["VSPlayerWeekdayTime"].get("StartHour", 20))
                    self.pvp_player_wday_end.set(pi["VSPlayerWeekdayTime"].get("EndHour", 22))
                if "VSPlayerWeekendTime" in pi:
                    self.pvp_player_wend_start.set(pi["VSPlayerWeekendTime"].get("StartHour", 20))
                    self.pvp_player_wend_end.set(pi["VSPlayerWeekendTime"].get("EndHour", 22))
                if "VSCastleWeekdayTime" in pi:
                    self.pvp_castle_wday_start.set(pi["VSCastleWeekdayTime"].get("StartHour", 20))
                    self.pvp_castle_wday_end.set(pi["VSCastleWeekdayTime"].get("EndHour", 22))
                if "VSCastleWeekendTime" in pi:
                    self.pvp_castle_wend_start.set(pi["VSCastleWeekendTime"].get("StartHour", 20))
                    self.pvp_castle_wend_end.set(pi["VSCastleWeekendTime"].get("EndHour", 22))
                we = game.get("WarEventGameSettings", {})
                if "Interval" in we: self.war_event_interval_var.set(we["Interval"])

                # VampireStatModifiers
                vsm = game.get("VampireStatModifiers", {})
                if "MaxHealthModifier"    in vsm: self.vamp_hp_var.set(vsm["MaxHealthModifier"])
                if "PhysicalPowerModifier"in vsm: self.vamp_phys_var.set(vsm["PhysicalPowerModifier"])
                if "SpellPowerModifier"   in vsm: self.vamp_spell_var.set(vsm["SpellPowerModifier"])

                # UnitStatModifiers_Global
                usm = game.get("UnitStatModifiers_Global", {})
                if "MaxHealthModifier" in usm: self.enemy_hp_var.set(usm["MaxHealthModifier"])
                if "PowerModifier"     in usm: self.enemy_power_var.set(usm["PowerModifier"])
                if "LevelIncrease"     in usm: self.enemy_level_var.set(usm["LevelIncrease"])

                # UnitStatModifiers_VBlood
                vbm = game.get("UnitStatModifiers_VBlood", {})
                if "MaxHealthModifier" in vbm: self.vblood_hp_var.set(vbm["MaxHealthModifier"])
                if "PowerModifier"     in vbm: self.vblood_pow_var.set(vbm["PowerModifier"])
                if "LevelIncrease"     in vbm: self.vblood_lvl_var.set(vbm["LevelIncrease"])

                # TraderModifiers
                tm = game.get("TraderModifiers", {})
                if "StockModifier"        in tm: self.trader_stock_var.set(tm["StockModifier"])
                if "PriceModifier"        in tm: self.trader_price_var.set(tm["PriceModifier"])
                if "RestockTimerModifier" in tm: self.trader_restock_var.set(tm["RestockTimerModifier"])

        return found_msg, checked

    # ── Load / Save UI values ────────────────────────────────────────────────
    def _load_ui_from_config(self):
        c = self.cfg
        self.path_var.set(c["server_path"])
        self.server_name_var.set(c["server_name"])
        self.description_var.set(c.get("description", ""))
        self.save_name_var.set(c.get("save_name", "world1"))
        self.password_var.set(c["password"])
        self.list_steam_var.set(c.get("list_steam", True))
        self.list_eos_var.set(c.get("list_eos", False))
        self.secure_var.set(c.get("secure", True))
        self.server_fps_var.set(c.get("server_fps", 30))
        self.max_admins_var.set(c.get("max_admins", 4))
        self.autosave_var.set(c["auto_save_interval"])
        self.autosave_count_var.set(c.get("auto_save_count", 20))
        self.compress_saves_var.set(c.get("compress_saves", True))
        self.cycle_entry_var.set(str(int(c["day_length_minutes"])))
        self.day_start_var.set(c["day_time_start"])
        self.day_end_var.set(c["day_time_end"])
        self.bm_freq_min_var.set(c.get("blood_moon_freq_min", 10))
        self.bm_freq_max_var.set(c.get("blood_moon_freq_max", 18))
        self.bm_dur_var.set(c["blood_moon_duration"])
        self.decay_var.set(c["castle_decay_rate"])
        self.drain_var.set(c["castle_blood_essence_drain"])
        self.xp_var.set(c["xp_multiplier"])
        self.drop_var.set(c["drop_table_modifier"])
        self.resource_var.set(c["resource_yield_modifier"])
        self.shard_var.set(c["soul_shard_modifier"])
        self.blood_essence_yield_var.set(c.get("blood_essence_yield", 1.0))
        self.inventory_stacks_var.set(c.get("inventory_stacks", 1.0))
        self.build_cost_var.set(c.get("build_cost", 1.0))
        self.craft_rate_var.set(c.get("craft_rate", 1.0))
        self.recipe_cost_var.set(c.get("recipe_cost", 1.0))
        self.research_cost_var.set(c.get("research_cost", 1.0))
        self.research_time_var.set(c.get("research_time", 1.0))
        self.refine_cost_var.set(c.get("refine_cost", 1.0))
        self.refine_rate_var.set(c.get("refine_rate", 1.0))
        self.dismantle_var.set(c.get("dismantle", 0.75))
        self.repair_cost_var.set(c.get("repair_cost", 1.0))
        self.vamp_hp_var.set(c.get("vamp_hp", 1.0))
        self.vamp_phys_var.set(c.get("vamp_phys", 1.0))
        self.vamp_spell_var.set(c.get("vamp_spell", 1.0))
        self.enemy_hp_var.set(c.get("enemy_hp", 1.0))
        self.enemy_power_var.set(c.get("enemy_power", 1.0))
        self.enemy_level_var.set(c.get("enemy_level", 0))
        self.vblood_hp_var.set(c.get("vblood_hp", 1.0))
        self.vblood_pow_var.set(c.get("vblood_power", 1.0))
        self.vblood_lvl_var.set(c.get("vblood_level", 0))
        self.trader_stock_var.set(c.get("trader_stock", 1.0))
        self.trader_price_var.set(c.get("trader_price", 1.0))
        self.trader_restock_var.set(c.get("trader_restock", 1.0))
        self.max_players_var.set(c["max_players"])
        self.pvp_var.set(c["pvp_enabled"])
        self.pvp_dmg_var.set(c["pvp_damage_modifier"])
        self.teleport_bound_var.set(c.get("teleport_bound_items", True))
        self.blood_bound_var.set(c.get("blood_bound_equipment", True))
        self.bat_bound_var.set(c.get("bat_bound_items", False))
        self.loot_containers_var.set(c.get("can_loot_enemy_containers", True))
        self.global_chat_var.set(c.get("global_chat", True))
        self.all_waypoints_var.set(c.get("all_waypoints_unlocked", False))
        self.clan_size_var.set(c.get("clan_size", 4))
        self.castle_reloc_var.set(c.get("castle_relocation_enabled", True))
        self.castle_reloc_cooldown_var.set(c.get("castle_relocation_cooldown", 10800))
        self.castle_min_dist_var.set(c.get("castle_min_distance", 2))
        self.free_castle_claim_var.set(c.get("free_castle_claim", False))
        self.free_castle_raid_var.set(c.get("free_castle_raid", False))
        self.free_castle_dest_var.set(c.get("free_castle_destroy", False))
        self.inactivity_kill_var.set(c.get("inactivity_kill_enabled", True))
        self.disconnected_dead_var.set(c.get("disconnected_dead_enabled", True))
        self.disconnected_dead_timer_var.set(c.get("disconnected_dead_timer", 60))
        self.disconnect_sun_var.set(c.get("disconnect_sun_immunity", 300))
        self.starting_level_var.set(c.get("starting_level", 0))
        self.pvp_player_wday_start.set(c.get("pvp_player_wday_start", 20))
        self.pvp_player_wday_end.set(c.get("pvp_player_wday_end", 22))
        self.pvp_player_wend_start.set(c.get("pvp_player_wend_start", 20))
        self.pvp_player_wend_end.set(c.get("pvp_player_wend_end", 22))
        self.pvp_castle_wday_start.set(c.get("pvp_castle_wday_start", 20))
        self.pvp_castle_wday_end.set(c.get("pvp_castle_wday_end", 22))
        self.pvp_castle_wend_start.set(c.get("pvp_castle_wend_start", 20))
        self.pvp_castle_wend_end.set(c.get("pvp_castle_wend_end", 22))
        self.pvp_protection_var.set(c.get("pvp_protection_mode", "Medium"))
        self.death_container_var.set(c.get("death_container_permission", "Anyone"))
        self.inventory_drop_var.set(c.get("inventory_drop_on_death", "Always"))
        self.siege_weapon_health_var.set(c.get("siege_weapon_health", "Normal"))
        self.announce_siege_var.set(c.get("announce_siege_spawn", True))
        self.show_siege_icon_var.set(c.get("show_siege_icon", False))
        self.war_event_interval_var.set(c.get("war_event_interval", 0))
        self.relic_spawn_var.set(c.get("relic_spawn_type", "Unique"))
        self.servant_var.set(c["servant_convert_rate"])
        self.blood_start_var.set(c["starting_blood_essence"])
        self.preset_var.set(c["global_settings_preset"])
        self.game_port_var.set(c["game_port"])
        self.query_port_var.set(c["query_port"])
        self.rcon_enabled_var.set(c.get("rcon_enabled", False))
        self.rcon_port_var.set(c.get("rcon_port", 25575))
        self.rcon_password_var.set(c.get("rcon_password", ""))

    def _collect_config_from_ui(self):
        self.cfg["server_path"]           = os.path.normpath(self.path_var.get().strip())
        self.cfg["server_name"]           = self.server_name_var.get().strip()
        self.cfg["description"]           = self.description_var.get()
        self.cfg["save_name"]             = self.save_name_var.get().strip()
        self.cfg["password"]              = self.password_var.get()
        self.cfg["list_steam"]            = bool(self.list_steam_var.get())
        self.cfg["list_eos"]              = bool(self.list_eos_var.get())
        self.cfg["secure"]                = bool(self.secure_var.get())
        self.cfg["server_fps"]            = int(self.server_fps_var.get())
        self.cfg["max_admins"]            = int(self.max_admins_var.get())
        self.cfg["auto_save_interval"]    = int(self.autosave_var.get())
        self.cfg["auto_save_count"]       = int(self.autosave_count_var.get())
        self.cfg["compress_saves"]        = bool(self.compress_saves_var.get())
        try:
            self.cfg["day_length_minutes"]  = float(self.cycle_entry_var.get())
        except ValueError:
            self.cfg["day_length_minutes"]  = 360.0
        self.cfg["night_length_minutes"] = float(self.night_len_var.get())
        self.cfg["day_time_start"]        = float(self.day_start_var.get())
        self.cfg["day_time_end"]          = float(self.day_end_var.get())
        self.cfg["blood_moon_freq_min"]   = int(self.bm_freq_min_var.get())
        self.cfg["blood_moon_freq_max"]   = int(self.bm_freq_max_var.get())
        self.cfg["blood_moon_duration"]   = float(self.bm_dur_var.get())
        self.cfg["castle_decay_rate"]     = float(self.decay_var.get())
        self.cfg["castle_blood_essence_drain"] = float(self.drain_var.get())
        self.cfg["xp_multiplier"]         = float(self.xp_var.get())
        self.cfg["drop_table_modifier"]   = float(self.drop_var.get())
        self.cfg["resource_yield_modifier"]= float(self.resource_var.get())
        self.cfg["soul_shard_modifier"]   = float(self.shard_var.get())
        self.cfg["blood_essence_yield"]   = float(self.blood_essence_yield_var.get())
        self.cfg["inventory_stacks"]      = float(self.inventory_stacks_var.get())
        self.cfg["build_cost"]            = float(self.build_cost_var.get())
        self.cfg["craft_rate"]            = float(self.craft_rate_var.get())
        self.cfg["recipe_cost"]           = float(self.recipe_cost_var.get())
        self.cfg["research_cost"]         = float(self.research_cost_var.get())
        self.cfg["research_time"]         = float(self.research_time_var.get())
        self.cfg["refine_cost"]           = float(self.refine_cost_var.get())
        self.cfg["refine_rate"]           = float(self.refine_rate_var.get())
        self.cfg["dismantle"]             = float(self.dismantle_var.get())
        self.cfg["repair_cost"]           = float(self.repair_cost_var.get())
        self.cfg["vamp_hp"]               = float(self.vamp_hp_var.get())
        self.cfg["vamp_phys"]             = float(self.vamp_phys_var.get())
        self.cfg["vamp_spell"]            = float(self.vamp_spell_var.get())
        self.cfg["enemy_hp"]              = float(self.enemy_hp_var.get())
        self.cfg["enemy_power"]           = float(self.enemy_power_var.get())
        self.cfg["enemy_level"]           = int(self.enemy_level_var.get())
        self.cfg["vblood_hp"]             = float(self.vblood_hp_var.get())
        self.cfg["vblood_power"]          = float(self.vblood_pow_var.get())
        self.cfg["vblood_level"]          = int(self.vblood_lvl_var.get())
        self.cfg["trader_stock"]          = float(self.trader_stock_var.get())
        self.cfg["trader_price"]          = float(self.trader_price_var.get())
        self.cfg["trader_restock"]        = float(self.trader_restock_var.get())
        self.cfg["max_players"]           = int(self.max_players_var.get())
        self.cfg["pvp_enabled"]               = bool(self.pvp_var.get())
        self.cfg["pvp_damage_modifier"]       = float(self.pvp_dmg_var.get())
        self.cfg["teleport_bound_items"]      = bool(self.teleport_bound_var.get())
        self.cfg["blood_bound_equipment"]     = bool(self.blood_bound_var.get())
        self.cfg["bat_bound_items"]           = bool(self.bat_bound_var.get())
        self.cfg["can_loot_enemy_containers"] = bool(self.loot_containers_var.get())
        self.cfg["global_chat"]               = bool(self.global_chat_var.get())
        self.cfg["all_waypoints_unlocked"]    = bool(self.all_waypoints_var.get())
        self.cfg["clan_size"]                 = int(self.clan_size_var.get())
        self.cfg["castle_relocation_enabled"] = bool(self.castle_reloc_var.get())
        self.cfg["castle_relocation_cooldown"]= int(self.castle_reloc_cooldown_var.get())
        self.cfg["castle_min_distance"]       = int(self.castle_min_dist_var.get())
        self.cfg["free_castle_claim"]         = bool(self.free_castle_claim_var.get())
        self.cfg["free_castle_raid"]          = bool(self.free_castle_raid_var.get())
        self.cfg["free_castle_destroy"]       = bool(self.free_castle_dest_var.get())
        self.cfg["inactivity_kill_enabled"]   = bool(self.inactivity_kill_var.get())
        self.cfg["disconnected_dead_enabled"] = bool(self.disconnected_dead_var.get())
        self.cfg["disconnected_dead_timer"]   = int(self.disconnected_dead_timer_var.get())
        self.cfg["disconnect_sun_immunity"]   = int(self.disconnect_sun_var.get())
        self.cfg["starting_level"]            = int(self.starting_level_var.get())
        self.cfg["pvp_player_wday_start"]     = int(self.pvp_player_wday_start.get())
        self.cfg["pvp_player_wday_end"]       = int(self.pvp_player_wday_end.get())
        self.cfg["pvp_player_wend_start"]     = int(self.pvp_player_wend_start.get())
        self.cfg["pvp_player_wend_end"]       = int(self.pvp_player_wend_end.get())
        self.cfg["pvp_castle_wday_start"]     = int(self.pvp_castle_wday_start.get())
        self.cfg["pvp_castle_wday_end"]       = int(self.pvp_castle_wday_end.get())
        self.cfg["pvp_castle_wend_start"]     = int(self.pvp_castle_wend_start.get())
        self.cfg["pvp_castle_wend_end"]       = int(self.pvp_castle_wend_end.get())
        self.cfg["pvp_protection_mode"]       = self.pvp_protection_var.get()
        self.cfg["death_container_permission"]= self.death_container_var.get()
        self.cfg["inventory_drop_on_death"]   = self.inventory_drop_var.get()
        self.cfg["siege_weapon_health"]       = self.siege_weapon_health_var.get()
        self.cfg["announce_siege_spawn"]      = bool(self.announce_siege_var.get())
        self.cfg["show_siege_icon"]           = bool(self.show_siege_icon_var.get())
        self.cfg["war_event_interval"]        = int(self.war_event_interval_var.get())
        self.cfg["relic_spawn_type"]          = self.relic_spawn_var.get()
        self.cfg["servant_convert_rate"]  = float(self.servant_var.get())
        self.cfg["starting_blood_essence"]= int(self.blood_start_var.get())
        self.cfg["global_settings_preset"]= self.preset_var.get()
        self.cfg["game_port"]             = int(self.game_port_var.get())
        self.cfg["query_port"]            = int(self.query_port_var.get())
        self.cfg["rcon_enabled"]          = bool(self.rcon_enabled_var.get())
        self.cfg["rcon_port"]             = int(self.rcon_port_var.get())
        self.cfg["rcon_password"]         = self.rcon_password_var.get()

    def _save_settings(self):
        self._collect_config_from_ui()
        save_config(self.cfg)
        self._write_server_settings()
        messagebox.showinfo("Saved", "Settings saved!\n\nRestart the server to apply changes.")

    # ── Read-then-merge helper ───────────────────────────────────────────────
    @staticmethod
    def _read_json_safe(path):
        """Load an existing JSON file, or return an empty dict if missing/corrupt."""
        if os.path.isfile(path):
            try:
                with open(path, "r", encoding="utf-8-sig") as f:  # utf-8-sig strips BOM
                    return json.load(f)
            except Exception:
                pass
        return {}

    # ── Write ServerGameSettings.json / ServerHostSettings.json ─────────────
    def _write_server_settings(self):
        """
        Reads each existing config file first, then updates ONLY the keys
        managed by this tool.  Everything else (admin lists, obscure flags,
        custom values you set by hand, etc.) is left completely untouched.
        """
        base = self.cfg["server_path"]
        if not base:
            return

        # Write to whichever Settings folder already has the files,
        # falling back to save-data\Settings if none exist yet.
        settings_dir = None
        for d in self._find_settings_dirs():
            if os.path.isfile(os.path.join(d, "ServerHostSettings.json")) or \
               os.path.isfile(os.path.join(d, "ServerGameSettings.json")):
                settings_dir = d
                break
        if not settings_dir:
            settings_dir = os.path.join(base, "save-data", "Settings")
        os.makedirs(settings_dir, exist_ok=True)

        # ── ServerGameSettings.json ──────────────────────────────────────────
        game_path = os.path.join(settings_dir, "ServerGameSettings.json")
        game_settings = self._read_json_safe(game_path)   # start from what's already there

        game_settings.update({
            "GameModeType":      "PvP" if self.cfg["pvp_enabled"] else "PvE",
            "CastleDamageMode":  "Always" if self.cfg["pvp_enabled"] else "Never",
            "PlayerDamageMode":  "Always" if self.cfg["pvp_enabled"] else "TimeRestricted",
            "CastleHeartDamageMode": "CanBeDestroyedByPlayers" if self.cfg["pvp_enabled"]
                                     else "CanBeSeizedOrDestroyedByPlayers",
            "TeleportBoundItems":              self.cfg.get("teleport_bound_items", True),
            "BloodBoundEquipment":             self.cfg.get("blood_bound_equipment", True),
            "BatBoundItems":                   self.cfg.get("bat_bound_items", False),
            "CanLootEnemyContainers":          self.cfg.get("can_loot_enemy_containers", True),
            "AllowGlobalChat":                 self.cfg.get("global_chat", True),
            "AllWaypointsUnlocked":            self.cfg.get("all_waypoints_unlocked", False),
            "ClanSize":                        self.cfg.get("clan_size", 4),
            "CastleRelocationEnabled":         self.cfg.get("castle_relocation_enabled", True),
            "CastleRelocationCooldown":        float(self.cfg.get("castle_relocation_cooldown", 10800)),
            "CastleMinimumDistanceInFloors":   self.cfg.get("castle_min_distance", 2),
            "FreeCastleClaim":                 self.cfg.get("free_castle_claim", False),
            "FreeCastleRaid":                  self.cfg.get("free_castle_raid", False),
            "FreeCastleDestroy":               self.cfg.get("free_castle_destroy", False),
            "InactivityKillEnabled":           self.cfg.get("inactivity_kill_enabled", True),
            "DisableDisconnectedDeadEnabled":  self.cfg.get("disconnected_dead_enabled", True),
            "DisableDisconnectedDeadTimer":    self.cfg.get("disconnected_dead_timer", 60),
            "DisconnectedSunImmunityTime":     float(self.cfg.get("disconnect_sun_immunity", 300)),
            "StartingProgressionLevel":        self.cfg.get("starting_level", 0),
            "PvPProtectionMode":               self.cfg.get("pvp_protection_mode", "Medium"),
            "DeathContainerPermission":        self.cfg.get("death_container_permission", "Anyone"),
            "InventoryDropOnDeath":            self.cfg.get("inventory_drop_on_death", "Always"),
            "SiegeWeaponHealth":               self.cfg.get("siege_weapon_health", "Normal"),
            "AnnounceSiegeWeaponSpawn":        self.cfg.get("announce_siege_spawn", True),
            "ShowSiegeWeaponMapIcon":          self.cfg.get("show_siege_icon", False),
            "RelicSpawnType":                  self.cfg.get("relic_spawn_type", "Unique"),
            "CastleDecayRateModifier":         self.cfg["castle_decay_rate"],
            "CastleBloodEssenceDrainModifier": self.cfg["castle_blood_essence_drain"],
            "ServantConvertRateModifier":      self.cfg["servant_convert_rate"],
            "MaterialYieldModifier_Global":    self.cfg["resource_yield_modifier"],
            "DropTableModifier_General":       self.cfg["drop_table_modifier"],
            "DropTableModifier_Humans":        self.cfg["drop_table_modifier"],
            "DropTableModifier_Plants":        self.cfg["drop_table_modifier"],
            "DropTableModifier_Undead":        self.cfg["drop_table_modifier"],
            "DropTableModifier_Demons":        self.cfg["drop_table_modifier"],
            "DropTableModifier_Mechs":         self.cfg["drop_table_modifier"],
            "DropTableModifier_Beasts":        self.cfg["drop_table_modifier"],
            "PlayerXPRate":                    self.cfg["xp_multiplier"],
            "SoulShardModifier":               self.cfg["soul_shard_modifier"],
            "BloodEssenceYieldModifier":       self.cfg["blood_essence_yield"],
            "InventoryStacksModifier":         self.cfg["inventory_stacks"],
            "BuildCostModifier":               self.cfg["build_cost"],
            "CraftRateModifier":               self.cfg["craft_rate"],
            "RecipeCostModifier":              self.cfg["recipe_cost"],
            "ResearchCostModifier":            self.cfg["research_cost"],
            "ResearchTimeModifier":            self.cfg["research_time"],
            "RefinementCostModifier":          self.cfg["refine_cost"],
            "RefinementRateModifier":          self.cfg["refine_rate"],
            "DismantleResourceModifier":       self.cfg["dismantle"],
            "RepairCostModifier":              self.cfg["repair_cost"],
            "PlayerStartingBloodEssence":      self.cfg["starting_blood_essence"],
            "AutoSaveInterval":                self.cfg["auto_save_interval"],
        })

        # ── Nested sections — merge carefully ────────────────────────────────
        gtm = game_settings.get("GameTimeModifiers", {})
        gtm.update({
            "DayDurationInSeconds":   self.cfg["day_length_minutes"] * 60,
            "DayStartHour":           int(self.cfg["day_time_start"]),
            "DayStartMinute":         0,
            "DayEndHour":             int(self.cfg["day_time_end"]),
            "DayEndMinute":           0,
            "BloodMoonFrequency_Min": self.cfg["blood_moon_freq_min"],
            "BloodMoonFrequency_Max": self.cfg["blood_moon_freq_max"],
            "BloodMoonBuff":          self.cfg["blood_moon_duration"],
        })
        game_settings["GameTimeModifiers"] = gtm

        vsm = game_settings.get("VampireStatModifiers", {})
        vsm.update({
            "MaxHealthModifier":     self.cfg["vamp_hp"],
            "PhysicalPowerModifier": self.cfg["vamp_phys"],
            "SpellPowerModifier":    self.cfg["vamp_spell"],
        })
        game_settings["VampireStatModifiers"] = vsm

        usm = game_settings.get("UnitStatModifiers_Global", {})
        usm.update({
            "MaxHealthModifier": self.cfg["enemy_hp"],
            "PowerModifier":     self.cfg["enemy_power"],
            "LevelIncrease":     self.cfg["enemy_level"],
        })
        game_settings["UnitStatModifiers_Global"] = usm

        vbm = game_settings.get("UnitStatModifiers_VBlood", {})
        vbm.update({
            "MaxHealthModifier": self.cfg["vblood_hp"],
            "PowerModifier":     self.cfg["vblood_power"],
            "LevelIncrease":     self.cfg["vblood_level"],
        })
        game_settings["UnitStatModifiers_VBlood"] = vbm

        tm = game_settings.get("TraderModifiers", {})
        tm.update({
            "StockModifier":        self.cfg["trader_stock"],
            "PriceModifier":        self.cfg["trader_price"],
            "RestockTimerModifier": self.cfg["trader_restock"],
        })
        game_settings["TraderModifiers"] = tm

        # ── PlayerInteractionSettings ────────────────────────────────────────
        pi = game_settings.get("PlayerInteractionSettings", {})
        pi["TimeZone"] = "Local"
        for key, start_val, end_val in [
            ("VSPlayerWeekdayTime",  self.cfg.get("pvp_player_wday_start", 20), self.cfg.get("pvp_player_wday_end", 22)),
            ("VSPlayerWeekendTime",  self.cfg.get("pvp_player_wend_start", 20), self.cfg.get("pvp_player_wend_end", 22)),
            ("VSCastleWeekdayTime",  self.cfg.get("pvp_castle_wday_start", 20), self.cfg.get("pvp_castle_wday_end", 22)),
            ("VSCastleWeekendTime",  self.cfg.get("pvp_castle_wend_start", 20), self.cfg.get("pvp_castle_wend_end", 22)),
        ]:
            existing = pi.get(key, {})
            existing.update({"StartHour": start_val, "StartMinute": 0,
                             "EndHour": end_val, "EndMinute": 0})
            pi[key] = existing
        game_settings["PlayerInteractionSettings"] = pi

        # ── WarEventGameSettings ─────────────────────────────────────────────
        we = game_settings.get("WarEventGameSettings", {})
        we["Interval"] = self.cfg.get("war_event_interval", 0)
        game_settings["WarEventGameSettings"] = we

        with open(game_path, "w", encoding="utf-8") as f:
            json.dump(game_settings, f, indent=2)

        # ── ServerHostSettings.json ──────────────────────────────────────────
        host_path = os.path.join(settings_dir, "ServerHostSettings.json")
        host_settings = self._read_json_safe(host_path)   # start from what's already there

        host_settings.update({
            "Name":                self.cfg["server_name"],
            "Description":         self.cfg.get("description", ""),
            "SaveName":            self.cfg.get("save_name", "world1"),
            "Port":                self.cfg["game_port"],
            "QueryPort":           self.cfg["query_port"],
            "MaxConnectedUsers":   self.cfg["max_players"],
            "MaxConnectedAdmins":  self.cfg.get("max_admins", 4),
            "ServerFps":           self.cfg.get("server_fps", 30),
            "Password":            self.cfg["password"],
            "Secure":              self.cfg.get("secure", True),
            "ListOnSteam":         self.cfg.get("list_steam", True),
            "ListOnEOS":           self.cfg.get("list_eos", False),
            "AutoSaveCount":       self.cfg.get("auto_save_count", 20),
            "AutoSaveInterval":    self.cfg["auto_save_interval"],
            "CompressSaveFiles":   self.cfg.get("compress_saves", True),
            "GameSettingsPreset":  self.cfg["global_settings_preset"],
            "Rcon": {
                "Enabled":  self.cfg.get("rcon_enabled", False),
                "Password": self.cfg.get("rcon_password", ""),
                "Port":     self.cfg.get("rcon_port", 25575),
            },
        })

        with open(host_path, "w", encoding="utf-8") as f:
            json.dump(host_settings, f, indent=2)

    # ── Server process control ───────────────────────────────────────────────
    def _browse_path(self):
        folder = filedialog.askdirectory(title=f"Select folder containing {SERVER_EXE}")
        if folder:
            self.path_var.set(folder)

    def _reload_from_server(self):
        """Re-read the server JSON files and push their values into the UI."""
        self.focus()  # take focus away from any field so Tkinter commits the value
        raw_path     = self.path_var.get().strip()
        current_path = os.path.normpath(raw_path) if raw_path else ""
        if not current_path or current_path == ".":
            messagebox.showerror("No Path", "Please set the server folder path on the Server tab first.")
            return

        # Update cfg with the clean path before anything else touches it
        self.cfg["server_path"] = current_path

        # Build paths directly here — don't rely on self.cfg round-trip
        settings_dir = os.path.join(current_path, "save-data", "Settings")
        host_file    = os.path.join(settings_dir, "ServerHostSettings.json")
        game_file    = os.path.join(settings_dir, "ServerGameSettings.json")

        found_msg = []
        host = self._read_json_safe(host_file)
        if host:
            found_msg.append(f"Host: {host_file}")
            if "Name"               in host: self.server_name_var.set(host["Name"])
            if "Description"        in host: self.description_var.set(host["Description"])
            if "Password"           in host: self.password_var.set(host["Password"])
            if "SaveName"           in host: self.save_name_var.set(host["SaveName"])
            if "Port"               in host: self.game_port_var.set(host["Port"])
            if "QueryPort"          in host: self.query_port_var.set(host["QueryPort"])
            if "MaxConnectedUsers"  in host: self.max_players_var.set(host["MaxConnectedUsers"])
            if "MaxConnectedAdmins" in host: self.max_admins_var.set(host["MaxConnectedAdmins"])
            if "ServerFps"          in host: self.server_fps_var.set(host["ServerFps"])
            if "AutoSaveInterval"   in host: self.autosave_var.set(host["AutoSaveInterval"])
            if "AutoSaveCount"      in host: self.autosave_count_var.set(host["AutoSaveCount"])
            if "CompressSaveFiles"  in host: self.compress_saves_var.set(host["CompressSaveFiles"])
            if "ListOnSteam"        in host: self.list_steam_var.set(host["ListOnSteam"])
            if "ListOnEOS"          in host: self.list_eos_var.set(host["ListOnEOS"])
            if "Secure"             in host: self.secure_var.set(host["Secure"])
            if "GameSettingsPreset" in host: self.preset_var.set(host["GameSettingsPreset"])
            if "Rcon" in host:
                rcon = host["Rcon"]
                if "Enabled"  in rcon: self.rcon_enabled_var.set(rcon["Enabled"])
                if "Port"     in rcon: self.rcon_port_var.set(rcon["Port"])
                if "Password" in rcon: self.rcon_password_var.set(rcon["Password"])

        game = self._read_json_safe(game_file)
        if game:
            found_msg.append(f"Game: {game_file}")
            gtm = game.get("GameTimeModifiers", {})
            if "DayDurationInSeconds"   in gtm:
                self.cycle_entry_var.set(str(int(gtm["DayDurationInSeconds"] / 60)))
            if "DayStartHour"           in gtm: self.day_start_var.set(gtm["DayStartHour"])
            if "DayEndHour"             in gtm: self.day_end_var.set(gtm["DayEndHour"])
            if "BloodMoonFrequency_Min" in gtm: self.bm_freq_min_var.set(gtm["BloodMoonFrequency_Min"])
            if "BloodMoonFrequency_Max" in gtm: self.bm_freq_max_var.set(gtm["BloodMoonFrequency_Max"])
            if "BloodMoonBuff"          in gtm: self.bm_dur_var.set(gtm["BloodMoonBuff"])

            if "CastleDecayRateModifier"         in game: self.decay_var.set(game["CastleDecayRateModifier"])
            if "CastleBloodEssenceDrainModifier" in game: self.drain_var.set(game["CastleBloodEssenceDrainModifier"])
            if "PlayerXPRate"                    in game: self.xp_var.set(game["PlayerXPRate"])
            if "DropTableModifier_General"       in game: self.drop_var.set(game["DropTableModifier_General"])
            if "MaterialYieldModifier_Global"    in game: self.resource_var.set(game["MaterialYieldModifier_Global"])
            if "SoulShardModifier"               in game: self.shard_var.set(game["SoulShardModifier"])
            if "BloodEssenceYieldModifier"       in game: self.blood_essence_yield_var.set(game["BloodEssenceYieldModifier"])
            if "InventoryStacksModifier"         in game: self.inventory_stacks_var.set(game["InventoryStacksModifier"])
            if "BuildCostModifier"               in game: self.build_cost_var.set(game["BuildCostModifier"])
            if "CraftRateModifier"               in game: self.craft_rate_var.set(game["CraftRateModifier"])
            if "RecipeCostModifier"              in game: self.recipe_cost_var.set(game["RecipeCostModifier"])
            if "ResearchCostModifier"            in game: self.research_cost_var.set(game["ResearchCostModifier"])
            if "ResearchTimeModifier"            in game: self.research_time_var.set(game["ResearchTimeModifier"])
            if "RefinementCostModifier"          in game: self.refine_cost_var.set(game["RefinementCostModifier"])
            if "RefinementRateModifier"          in game: self.refine_rate_var.set(game["RefinementRateModifier"])
            if "DismantleResourceModifier"       in game: self.dismantle_var.set(game["DismantleResourceModifier"])
            if "RepairCostModifier"              in game: self.repair_cost_var.set(game["RepairCostModifier"])
            if "ServantConvertRateModifier"      in game: self.servant_var.set(game["ServantConvertRateModifier"])
            if "PlayerStartingBloodEssence"      in game: self.blood_start_var.set(game["PlayerStartingBloodEssence"])
            if "GameModeType"                    in game: self.pvp_var.set(game["GameModeType"] == "PvP")
            if "AutoSaveInterval"                in game: self.autosave_var.set(game["AutoSaveInterval"])
            if "TeleportBoundItems"              in game: self.teleport_bound_var.set(game["TeleportBoundItems"])
            if "BloodBoundEquipment"             in game: self.blood_bound_var.set(game["BloodBoundEquipment"])
            if "BatBoundItems"                   in game: self.bat_bound_var.set(game["BatBoundItems"])
            if "CanLootEnemyContainers"          in game: self.loot_containers_var.set(game["CanLootEnemyContainers"])
            if "AllowGlobalChat"                 in game: self.global_chat_var.set(game["AllowGlobalChat"])
            if "AllWaypointsUnlocked"            in game: self.all_waypoints_var.set(game["AllWaypointsUnlocked"])
            if "ClanSize"                        in game: self.clan_size_var.set(game["ClanSize"])
            if "CastleRelocationEnabled"         in game: self.castle_reloc_var.set(game["CastleRelocationEnabled"])
            if "CastleRelocationCooldown"        in game: self.castle_reloc_cooldown_var.set(int(game["CastleRelocationCooldown"]))
            if "CastleMinimumDistanceInFloors"   in game: self.castle_min_dist_var.set(game["CastleMinimumDistanceInFloors"])
            if "FreeCastleClaim"                 in game: self.free_castle_claim_var.set(game["FreeCastleClaim"])
            if "FreeCastleRaid"                  in game: self.free_castle_raid_var.set(game["FreeCastleRaid"])
            if "FreeCastleDestroy"               in game: self.free_castle_dest_var.set(game["FreeCastleDestroy"])
            if "InactivityKillEnabled"           in game: self.inactivity_kill_var.set(game["InactivityKillEnabled"])
            if "DisableDisconnectedDeadEnabled"  in game: self.disconnected_dead_var.set(game["DisableDisconnectedDeadEnabled"])
            if "DisableDisconnectedDeadTimer"    in game: self.disconnected_dead_timer_var.set(game["DisableDisconnectedDeadTimer"])
            if "DisconnectedSunImmunityTime"     in game: self.disconnect_sun_var.set(int(game["DisconnectedSunImmunityTime"]))
            if "StartingProgressionLevel"        in game: self.starting_level_var.set(game["StartingProgressionLevel"])
            if "PvPProtectionMode"               in game: self.pvp_protection_var.set(game["PvPProtectionMode"])
            if "DeathContainerPermission"        in game: self.death_container_var.set(game["DeathContainerPermission"])
            if "InventoryDropOnDeath"            in game: self.inventory_drop_var.set(game["InventoryDropOnDeath"])
            if "SiegeWeaponHealth"               in game: self.siege_weapon_health_var.set(game["SiegeWeaponHealth"])
            if "AnnounceSiegeWeaponSpawn"        in game: self.announce_siege_var.set(game["AnnounceSiegeWeaponSpawn"])
            if "ShowSiegeWeaponMapIcon"          in game: self.show_siege_icon_var.set(game["ShowSiegeWeaponMapIcon"])
            if "RelicSpawnType"                  in game: self.relic_spawn_var.set(game["RelicSpawnType"])
            pi = game.get("PlayerInteractionSettings", {})
            if "VSPlayerWeekdayTime" in pi:
                self.pvp_player_wday_start.set(pi["VSPlayerWeekdayTime"].get("StartHour", 20))
                self.pvp_player_wday_end.set(pi["VSPlayerWeekdayTime"].get("EndHour", 22))
            if "VSPlayerWeekendTime" in pi:
                self.pvp_player_wend_start.set(pi["VSPlayerWeekendTime"].get("StartHour", 20))
                self.pvp_player_wend_end.set(pi["VSPlayerWeekendTime"].get("EndHour", 22))
            if "VSCastleWeekdayTime" in pi:
                self.pvp_castle_wday_start.set(pi["VSCastleWeekdayTime"].get("StartHour", 20))
                self.pvp_castle_wday_end.set(pi["VSCastleWeekdayTime"].get("EndHour", 22))
            if "VSCastleWeekendTime" in pi:
                self.pvp_castle_wend_start.set(pi["VSCastleWeekendTime"].get("StartHour", 20))
                self.pvp_castle_wend_end.set(pi["VSCastleWeekendTime"].get("EndHour", 22))
            we = game.get("WarEventGameSettings", {})
            if "Interval" in we: self.war_event_interval_var.set(we["Interval"])

            vsm = game.get("VampireStatModifiers", {})
            if "MaxHealthModifier"     in vsm: self.vamp_hp_var.set(vsm["MaxHealthModifier"])
            if "PhysicalPowerModifier" in vsm: self.vamp_phys_var.set(vsm["PhysicalPowerModifier"])
            if "SpellPowerModifier"    in vsm: self.vamp_spell_var.set(vsm["SpellPowerModifier"])

            usm = game.get("UnitStatModifiers_Global", {})
            if "MaxHealthModifier" in usm: self.enemy_hp_var.set(usm["MaxHealthModifier"])
            if "PowerModifier"     in usm: self.enemy_power_var.set(usm["PowerModifier"])
            if "LevelIncrease"     in usm: self.enemy_level_var.set(usm["LevelIncrease"])

            vbm = game.get("UnitStatModifiers_VBlood", {})
            if "MaxHealthModifier" in vbm: self.vblood_hp_var.set(vbm["MaxHealthModifier"])
            if "PowerModifier"     in vbm: self.vblood_pow_var.set(vbm["PowerModifier"])
            if "LevelIncrease"     in vbm: self.vblood_lvl_var.set(vbm["LevelIncrease"])

            tm = game.get("TraderModifiers", {})
            if "StockModifier"        in tm: self.trader_stock_var.set(tm["StockModifier"])
            if "PriceModifier"        in tm: self.trader_price_var.set(tm["PriceModifier"])
            if "RestockTimerModifier" in tm: self.trader_restock_var.set(tm["RestockTimerModifier"])

        if found_msg:
            messagebox.showinfo("Reloaded", "Sliders updated from:\n\n" + "\n".join(found_msg))
        else:
            messagebox.showwarning("Not Found",
                f"Files exist but could not be read.\n\nChecked:\n{host_file}\n{game_file}")

    def _get_exe_path(self):
        folder = self.path_var.get().strip()
        if not folder:
            messagebox.showerror("No Path", "Please set the server folder path on the Server tab first.")
            return None
        exe = os.path.join(folder, SERVER_EXE)
        if not os.path.isfile(exe):
            messagebox.showerror("Not Found",
                f"Could not find {SERVER_EXE} in:\n{folder}\n\nCheck the path on the Server tab.")
            return None
        return exe

    def _start_server(self):
        exe = self._get_exe_path()
        if not exe:
            return
        self._collect_config_from_ui()
        save_config(self.cfg)
        self._write_server_settings()

        try:
            self.server_process = subprocess.Popen(
                [exe,
                 "-persistentDataPath", os.path.join(self.cfg["server_path"], "save-data"),
                 "-serverName", self.cfg["server_name"],
                 "-logFile", os.path.join(self.cfg["server_path"], "logs", "VRisingServer.log"),
                ],
                cwd=self.cfg["server_path"],
                creationflags=subprocess.CREATE_NEW_CONSOLE  # Opens its own console window
            )
            self._set_status("running")
        except Exception as e:
            messagebox.showerror("Start Failed", f"Could not start server:\n{e}")

    def _stop_server(self):
        stopped = False

        # Method 1: taskkill — works even when psutil can't terminate due to permissions
        try:
            result = subprocess.run(
                ["taskkill", "/F", "/IM", SERVER_EXE],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                stopped = True
            elif "not found" in result.stderr.lower() or "no tasks" in result.stdout.lower():
                # Process wasn't running — that's fine
                stopped = True
        except Exception:
            pass

        # Method 2: psutil fallback if taskkill didn't work
        if not stopped:
            for proc in psutil.process_iter(["pid", "name", "exe"]):
                try:
                    name = (proc.info["name"] or "").lower()
                    exe  = (proc.info["exe"]  or "").lower()
                    if "vrisingserver" in name or "vrisingserver" in exe:
                        for child in proc.children(recursive=True):
                            child.kill()
                        proc.kill()
                        stopped = True
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        # Method 3: stored subprocess handle fallback
        if not stopped and self.server_process:
            try:
                self.server_process.kill()
                stopped = True
            except Exception:
                pass

        if not stopped:
            messagebox.showwarning("Could Not Stop",
                "Could not terminate the server automatically.\n\n"
                "Please close the server console window manually,\n"
                "then try again.")
            return

        self.server_process = None
        self._set_status("stopped")

    def _set_status(self, state):
        if state == "running":
            self.status_dot.config(fg=self.GREEN)
            self.status_label.config(text="Server: Running", fg=self.GREEN)
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")
        elif state == "stopped":
            self.status_dot.config(fg="#555")
            self.status_label.config(text="Server: Stopped", fg=self.TEXT_DIM)
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.cpu_label.config(text="")

    # ── Background monitor thread ────────────────────────────────────────────
    def _find_server_process(self):
        """Scan running processes for VRisingServer.exe.
        If this profile has an install path, only match a process whose
        executable is under that directory — so two servers on the same
        machine don't get confused with each other."""
        install_dir = self.cfg.get("server_path", "").strip().lower().rstrip("\\/")

        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                name = (proc.info["name"] or "").lower()
                exe  = (proc.info["exe"]  or "").lower()
                if "vrisingserver" not in name and "vrisingserver" not in exe:
                    continue
                # If install_dir is set, require the exe to be under it
                if install_dir and exe and not exe.startswith(install_dir):
                    continue
                return proc
            except psutil.AccessDenied:
                try:
                    pname = (proc.name() or "").lower()
                    if "vrisingserver" in pname and not install_dir:
                        return proc
                except Exception:
                    pass
            except psutil.NoSuchProcess:
                pass
        return None

    def _start_monitor(self):
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def _monitor_loop(self):
        while self._running:
            # If we don't have a process handle, check if one is already running
            if not self.server_process:
                found = self._find_server_process()
                if found:
                    self.server_process = found
                    self.after(0, lambda: self._set_status("running"))

            if self.server_process:
                try:
                    if isinstance(self.server_process, psutil.Process):
                        if not self.server_process.is_running():
                            self.server_process = None
                            self.after(0, lambda: self._set_status("stopped"))
                        else:
                            try:
                                cpu = self.server_process.cpu_percent(interval=1)
                                mem = self.server_process.memory_info().rss / (1024 * 1024)
                                txt = f"CPU: {cpu:.1f}%   RAM: {mem:.0f} MB"
                            except psutil.AccessDenied:
                                txt = "Running"
                            self.after(0, lambda t=txt: self.cpu_label.config(text=t))
                    else:
                        # subprocess.Popen
                        if self.server_process.poll() is not None:
                            self.server_process = None
                            self.after(0, lambda: self._set_status("stopped"))
                        else:
                            try:
                                proc = psutil.Process(self.server_process.pid)
                                cpu  = proc.cpu_percent(interval=1)
                                mem  = proc.memory_info().rss / (1024 * 1024)
                                txt  = f"CPU: {cpu:.1f}%   RAM: {mem:.0f} MB"
                            except psutil.AccessDenied:
                                txt = "Running"
                            self.after(0, lambda t=txt: self.cpu_label.config(text=t))
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    self.server_process = None
                    self.after(0, lambda: self._set_status("stopped"))
                except Exception:
                    pass

            time.sleep(2)

    # ── Clean shutdown ───────────────────────────────────────────────────────
    def _on_close(self):
        self._running = False
        if self.server_process:
            if messagebox.askyesno("Server Running",
                                   "The server is still running.\nStop it before closing?"):
                self._stop_server()
        self.destroy()

    def _switch_profile(self):
        """Show the profile picker and reload if the user chooses a different profile.
        Switching is always allowed — the current server (if running) keeps running
        untouched; the manager just stops watching it and starts watching the new profile's server."""
        picker = ProfilePicker(self)
        self.wait_window(picker)
        chosen = picker.chosen
        if not chosen or chosen == self.profile_name:
            return

        # Save current profile first
        save_config(self.cfg)

        # Drop the reference to the current server process — we're no longer managing it.
        # It keeps running; we just stop tracking it in this session.
        self.server_process = None

        # Switch and reload
        _set_active_profile(chosen)
        self.profile_name = chosen
        self._profile_lbl.config(text=f"Profile: {chosen}")
        self.cfg = load_config()
        self._load_ui_from_config()
        self._import_from_server_files()
        # Let the monitor pick up the new profile's server if it's already running
        self._set_status("stopped")


if __name__ == "__main__":
    import traceback
    try:
        # ── Migrate any legacy single-file config into a Default profile ──
        _migrate_legacy()

        # ── Profile picker ────────────────────────────────────────────────
        _root = tk.Tk()
        _root.withdraw()   # hide the blank root while picker is open

        picker = ProfilePicker(_root)
        _root.wait_window(picker)

        chosen = picker.chosen
        _root.destroy()

        if not chosen:
            # User closed the picker without selecting — exit cleanly
            raise SystemExit(0)

        _set_active_profile(chosen)

        # ── Launch main window ────────────────────────────────────────────
        app = VRisingManager(profile_name=chosen)
        app.mainloop()
    except Exception as e:
        # Show the full error in a message box and also print it
        err = traceback.format_exc()
        print(err)
        try:
            import tkinter as _tk
            import tkinter.messagebox as _mb
            root = _tk.Tk()
            root.withdraw()
            _mb.showerror("Startup Error",
                f"The manager failed to start:\n\n{err}\n\n"
                "Please copy this error and report it.")
            root.destroy()
        except Exception:
            pass
        input("Press Enter to close...")
