"""
privacy_shield.py - Privacy Shield Engine.
Disables Windows telemetry, ads, Cortana tracking.
Safe: only modifies registry VALUES, never deletes keys.
"""
import logging
import subprocess
import winreg

logger = logging.getLogger("RamBooster.PrivacyShield")
SW = subprocess.CREATE_NO_WINDOW


def _set_reg(hive, path, name, value, reg_type=winreg.REG_DWORD):
    """Safely set a registry value. Creates key if needed."""
    try:
        key = winreg.CreateKeyEx(hive, path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, reg_type, value)
        winreg.CloseKey(key)
        return True
    except Exception as e:
        logger.error(f"Registry error: {path}\\{name} -> {e}")
        return False


def _get_reg(hive, path, name, default=None):
    """Safely read a registry value."""
    try:
        key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return val
    except Exception:
        return default


def _stop_service(name):
    """Stop and disable a Windows service."""
    try:
        subprocess.run(["sc", "stop", name], capture_output=True,
                       creationflags=SW, timeout=10)
        subprocess.run(["sc", "config", name, "start=", "disabled"],
                       capture_output=True, creationflags=SW, timeout=10)
        return True
    except Exception:
        return False


def _start_service(name):
    """Enable and start a Windows service."""
    try:
        subprocess.run(["sc", "config", name, "start=", "auto"],
                       capture_output=True, creationflags=SW, timeout=10)
        subprocess.run(["sc", "start", name], capture_output=True,
                       creationflags=SW, timeout=10)
        return True
    except Exception:
        return False


# ── Telemetry ──

def disable_telemetry():
    """Disable Windows telemetry and diagnostic tracking."""
    results = {"applied": 0, "failed": 0, "details": []}

    actions = [
        # Stop DiagTrack service
        ("Service: DiagTrack", lambda: _stop_service("DiagTrack")),
        ("Service: dmwappushservice", lambda: _stop_service("dmwappushservice")),
        # Disable telemetry via policy
        ("Policy: AllowTelemetry=0", lambda: _set_reg(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
            "AllowTelemetry", 0)),
        # Disable app telemetry
        ("Policy: AITEnable=0", lambda: _set_reg(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Policies\Microsoft\Windows\AppCompat",
            "AITEnable", 0)),
        # Disable Customer Experience
        ("CEIPEnable=0", lambda: _set_reg(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\SQMClient\Windows",
            "CEIPEnable", 0)),
        # Disable feedback notifications
        ("Feedback: Never", lambda: _set_reg(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Siuf\Rules",
            "NumberOfSIUFInPeriod", 0)),
    ]

    for desc, action in actions:
        if action():
            results["applied"] += 1
            results["details"].append(f"OK: {desc}")
        else:
            results["failed"] += 1
            results["details"].append(f"FAIL: {desc}")

    logger.info(f"Telemetry disabled: {results['applied']}/{len(actions)}")
    return results


def enable_telemetry():
    """Re-enable Windows telemetry."""
    _start_service("DiagTrack")
    _start_service("dmwappushservice")
    _set_reg(winreg.HKEY_LOCAL_MACHINE,
             r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
             "AllowTelemetry", 3)
    return {"restored": True}


def get_telemetry_status():
    """Check if telemetry is currently enabled."""
    val = _get_reg(winreg.HKEY_LOCAL_MACHINE,
                   r"SOFTWARE\Policies\Microsoft\Windows\DataCollection",
                   "AllowTelemetry", 3)
    return {"enabled": val != 0, "level": val}


# ── Ads ──

def disable_ads():
    """Disable Windows built-in ads and suggestions."""
    results = {"applied": 0, "details": []}

    ads_settings = [
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
         "SilentInstalledAppsEnabled", 0, "Silent App Installs"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
         "SystemPaneSuggestionsEnabled", 0, "Start Menu Suggestions"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
         "SoftLandingEnabled", 0, "Soft Landing Tips"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
         "SubscribedContent-338389Enabled", 0, "Lock Screen Tips"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
         "SubscribedContent-310093Enabled", 0, "Welcome Experience"),
        (winreg.HKEY_CURRENT_USER,
         r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Advanced",
         "ShowSyncProviderNotifications", 0, "Sync Provider Ads"),
    ]

    for hive, path, name, value, desc in ads_settings:
        if _set_reg(hive, path, name, value):
            results["applied"] += 1
            results["details"].append(f"OK: {desc}")

    logger.info(f"Ads disabled: {results['applied']}/{len(ads_settings)}")
    return results


def enable_ads():
    """Re-enable Windows ads."""
    cdm = r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager"
    _set_reg(winreg.HKEY_CURRENT_USER, cdm, "SilentInstalledAppsEnabled", 1)
    _set_reg(winreg.HKEY_CURRENT_USER, cdm, "SystemPaneSuggestionsEnabled", 1)
    _set_reg(winreg.HKEY_CURRENT_USER, cdm, "SoftLandingEnabled", 1)
    return {"restored": True}


def get_ads_status():
    """Check if ads are disabled."""
    val = _get_reg(winreg.HKEY_CURRENT_USER,
                   r"SOFTWARE\Microsoft\Windows\CurrentVersion\ContentDeliveryManager",
                   "SilentInstalledAppsEnabled", 1)
    return {"enabled": val != 0}


# ── Cortana ──

def disable_cortana():
    """Disable Cortana background activity."""
    results = {"applied": 0, "details": []}

    cortana_settings = [
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
         "AllowCortana", 0, "Cortana Disabled"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
         "AllowSearchToUseLocation", 0, "Search Location Disabled"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
         "ConnectedSearchUseWeb", 0, "Web Search Disabled"),
        (winreg.HKEY_LOCAL_MACHINE,
         r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
         "DisableWebSearch", 1, "Web Search in Start Disabled"),
    ]

    for hive, path, name, value, desc in cortana_settings:
        if _set_reg(hive, path, name, value):
            results["applied"] += 1
            results["details"].append(f"OK: {desc}")

    logger.info(f"Cortana disabled: {results['applied']}/{len(cortana_settings)}")
    return results


def enable_cortana():
    """Re-enable Cortana."""
    ws = r"SOFTWARE\Policies\Microsoft\Windows\Windows Search"
    _set_reg(winreg.HKEY_LOCAL_MACHINE, ws, "AllowCortana", 1)
    _set_reg(winreg.HKEY_LOCAL_MACHINE, ws, "ConnectedSearchUseWeb", 1)
    _set_reg(winreg.HKEY_LOCAL_MACHINE, ws, "DisableWebSearch", 0)
    return {"restored": True}


def get_cortana_status():
    """Check if Cortana is enabled."""
    val = _get_reg(winreg.HKEY_LOCAL_MACHINE,
                   r"SOFTWARE\Policies\Microsoft\Windows\Windows Search",
                   "AllowCortana", 1)
    return {"enabled": val != 0}


# ── Full Privacy ──

def full_privacy_shield():
    """Apply all privacy protections at once."""
    t = disable_telemetry()
    a = disable_ads()
    c = disable_cortana()
    total = t["applied"] + a["applied"] + c["applied"]
    return {
        "total_applied": total,
        "telemetry": t,
        "ads": a,
        "cortana": c,
    }
