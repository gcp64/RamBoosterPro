"""
game_mode.py - Game Mode / CPU Boost Engine.
Stops unnecessary Windows services and optimizes CPU for gaming.
"""
import ctypes
import logging
import subprocess
import os

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


def _set_process_priority(priority_class=0x00000100):
    """Set current process to HIGH priority. 0x100 = REALTIME, 0x80 = HIGH."""
    try:
        handle = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.kernel32.SetPriorityClass(handle, priority_class)
        return True
    except Exception:
        return False


def _set_power_plan(plan="high"):
    """Set Windows power plan."""
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


def _disable_visual_effects():
    """Reduce Windows visual effects for performance."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 2)  # 2 = Best Performance
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def _restore_visual_effects():
    """Restore Windows visual effects."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\VisualEffects",
            0, winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, "VisualFXSetting", 0, winreg.REG_DWORD, 0)  # 0 = Let Windows choose
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def activate_game_mode():
    """Activate Game Mode - stop services, boost CPU, set power plan."""
    global _game_mode_active, _stopped_services
    _stopped_services = []
    results = {
        "services_stopped": 0,
        "services_failed": 0,
        "power_plan": False,
        "priority_boost": False,
        "visual_effects": False,
        "details": [],
    }

    # 1. Stop non-essential services
    for svc in GAMING_STOP_SERVICES:
        if _run_sc("stop", svc):
            _stopped_services.append(svc)
            results["services_stopped"] += 1
            results["details"].append(f"Stopped: {svc}")
        else:
            results["services_failed"] += 1

    # 2. Set HIGH power plan
    results["power_plan"] = _set_power_plan("high")

    # 3. Boost process priority
    results["priority_boost"] = _set_process_priority(0x00000080)  # HIGH

    # 4. Reduce visual effects
    results["visual_effects"] = _disable_visual_effects()

    _game_mode_active = True
    logger.info(
        f"Game Mode ON: {results['services_stopped']} services stopped, "
        f"power={results['power_plan']}"
    )
    return results


def deactivate_game_mode():
    """Deactivate Game Mode - restart services, restore settings."""
    global _game_mode_active, _stopped_services
    results = {
        "services_restarted": 0,
        "power_plan": False,
        "visual_restored": False,
    }

    # 1. Restart stopped services
    for svc in _stopped_services:
        if _run_sc("start", svc):
            results["services_restarted"] += 1

    # 2. Restore balanced power plan
    results["power_plan"] = _set_power_plan("balanced")

    # 3. Restore visual effects
    results["visual_restored"] = _restore_visual_effects()

    _stopped_services = []
    _game_mode_active = False
    logger.info(f"Game Mode OFF: {results['services_restarted']} services restarted")
    return results


def is_game_mode_active():
    return _game_mode_active
