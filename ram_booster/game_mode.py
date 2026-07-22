"""
game_mode.py - Game Mode / CPU & GPU Boost Engine.
Stops unnecessary Windows services and optimizes CPU & GPU for Games (Roblox, Genshin Impact, PUBG, Fortnite, etc.).
"""
import ctypes
import logging
import subprocess
import os
import winreg

logger = logging.getLogger("RamBooster.GameMode")

# Services safe to stop for gaming (non-critical background services)
GAMING_STOP_SERVICES = [
    "SysMain",           # Superfetch - preloads apps, uses RAM/CPU
    "DiagTrack",         # Diagnostics Tracking - telemetry
    "WSearch",           # Windows Search indexer
    "TabletInputService",# Touch keyboard
    "MapsBroker",        # Maps data
    "lfsvc",             # Geolocation
    "wisvc",             # Windows Insider
    "RetailDemo",        # Retail demo
    "WMPNetworkSvc",     # WMP sharing
    "XblAuthManager",    # Xbox auth (if not using Xbox)
    "XblGameSave",       # Xbox game save
    "XboxNetApiSvc",     # Xbox networking
    "XboxGipSvc",        # Xbox accessories
    "WbioSrvc",          # Biometric service
    "WerSvc",            # Windows Error Reporting
    "wuauserv",          # Windows Update (temp disable)
    "BITS",              # Background transfer
    "DoSvc",             # Delivery Optimization
    "InstallService",    # Microsoft Store install
]

_game_mode_active = False
_stopped_services = []


def _is_service_running(service):
    """Check if a Windows service is currently running."""
    try:
        result = subprocess.run(
            ["sc", "query", service],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return "RUNNING" in result.stdout
    except Exception:
        return False


def _run_sc(action, service):
    """Run sc.exe to start/stop a service."""
    try:
        result = subprocess.run(
            ["sc", action, service],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return result.returncode == 0
    except Exception:
        return False


def _set_process_priority(priority_class=0x00000080):
    """Set current process priority. 0x80 = HIGH, 0x8000 = ABOVE_NORMAL."""
    try:
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetPriorityClass(handle, priority_class)
        return True
    except Exception:
        return False


def _set_power_plan(plan="high"):
    """Set Windows power plan to High Performance."""
    plans = {
        "high": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
    }
    guid = plans.get(plan, plans["high"])
    try:
        subprocess.run(
            ["powercfg", "/setactive", guid],
            capture_output=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True
    except Exception:
        return False


def optimize_roblox_and_genshin():
    """
    Apply specialized Windows GPU & CPU High-Performance preferences for Roblox & Genshin Impact.
    - Forces High Performance GPU in DirectX UserGpuPreferences
    - Disables Windows Game Bar DVR throttling
    - Sets process priority boost
    """
    applied = []
    try:
        # Enable High Performance GPU for Roblox & Genshin in Registry
        key_path = r"Software\Microsoft\DirectX\UserGpuPreferences"
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            # 2 = High Performance GPU (Discrete NVIDIA / AMD)
            winreg.SetValueEx(key, "RobloxPlayerBeta.exe", 0, winreg.REG_SZ, "GpuPreference=2;")
            winreg.SetValueEx(key, "GenshinImpact.exe", 0, winreg.REG_SZ, "GpuPreference=2;")
            winreg.SetValueEx(key, "YuanShen.exe", 0, winreg.REG_SZ, "GpuPreference=2;")
            winreg.CloseKey(key)
            applied.append("Roblox & Genshin Impact GPU High Performance Preference: Active")
        except Exception:
            pass

        # Disable Game Bar DVR Throttling
        try:
            dvr_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"System\GameConfigStore")
            winreg.SetValueEx(dvr_key, "GameDVR_Enabled", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(dvr_key)
            applied.append("Game Bar DVR Throttling: Disabled for Zero Stuttering")
        except Exception:
            pass

        # Boost priority of active Roblox & Genshin Impact processes via PowerShell
        ps_cmd = "Get-Process -Name 'RobloxPlayerBeta','GenshinImpact','YuanShen' -ErrorAction SilentlyContinue | ForEach-Object { $_.PriorityClass = 'High' }"
        subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        applied.append("Active Roblox / Genshin Impact Process Priority: High")

        return {"success": True, "applied": applied}
    except Exception as e:
        return {"success": False, "error": str(e)}


def activate_game_mode():
    """Activate Game Mode."""
    global _game_mode_active, _stopped_services
    if _game_mode_active:
        return {"already_active": True, "services_stopped": len(_stopped_services)}

    _stopped_services = []
    for service in GAMING_STOP_SERVICES:
        if _is_service_running(service):
            if _run_sc("stop", service):
                _stopped_services.append(service)

    _set_power_plan("high")
    _set_process_priority(0x00000080)
    optimize_roblox_and_genshin()

    _game_mode_active = True
    logger.info(f"Game Mode activated: {len(_stopped_services)} services stopped.")
    return {
        "active": True,
        "services_stopped": len(_stopped_services),
        "stopped_list": _stopped_services,
        "power_plan": "High Performance",
        "priority": "HIGH",
    }


def deactivate_game_mode():
    """Deactivate Game Mode."""
    global _game_mode_active, _stopped_services
    if not _game_mode_active:
        return {"already_inactive": True}

    restarted = []
    for service in _stopped_services:
        if _run_sc("start", service):
            restarted.append(service)

    _set_power_plan("balanced")
    _set_process_priority(0x00000020)

    _stopped_services = []
    _game_mode_active = False
    logger.info(f"Game Mode deactivated: {len(restarted)} services restarted.")
    return {
        "active": False,
        "services_restarted": len(restarted),
        "power_plan": "Balanced",
    }


def is_game_mode_active():
    return _game_mode_active
