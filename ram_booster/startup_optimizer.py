"""
startup_optimizer.py - Startup Optimizer Engine.
Reads and manages Windows startup programs from Registry.
Safe: stores disabled entries in a backup key, never deletes originals permanently.
"""
import logging
import winreg
import os

logger = logging.getLogger("RamBooster.StartupOptimizer")

STARTUP_PATHS = [
    (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKCU"),
    (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Run", "HKLM"),
]

BACKUP_KEY = r"Software\RamBoosterPro\DisabledStartup"


def get_startup_programs():
    """Read all startup programs from registry."""
    programs = []
    for hive, path, hive_name in STARTUP_PATHS:
        try:
            key = winreg.OpenKey(hive, path, 0, winreg.KEY_READ)
            i = 0
            while True:
                try:
                    name, value, vtype = winreg.EnumValue(key, i)
                    programs.append({
                        "name": name,
                        "path": value,
                        "hive": hive_name,
                        "enabled": True,
                        "registry_path": path,
                    })
                    i += 1
                except OSError:
                    break
            winreg.CloseKey(key)
        except Exception as e:
            logger.error(f"Error reading {hive_name}: {e}")

    # Check disabled programs (our backup)
    try:
        bkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, BACKUP_KEY, 0, winreg.KEY_READ)
        i = 0
        while True:
            try:
                name, value, vtype = winreg.EnumValue(bkey, i)
                # Parse stored format: "HIVE|REGPATH|EXEPATH"
                parts = value.split("|", 2)
                if len(parts) == 3:
                    hive_name, reg_path, exe_path = parts
                    # Only add if not already in enabled list
                    if not any(p["name"] == name for p in programs):
                        programs.append({
                            "name": name,
                            "path": exe_path,
                            "hive": hive_name,
                            "enabled": False,
                            "registry_path": reg_path,
                        })
                i += 1
            except OSError:
                break
        winreg.CloseKey(bkey)
    except Exception:
        pass  # No backup key yet

    return programs


def disable_startup(name, hive_name, registry_path):
    """Disable a startup program by moving it to backup and removing from Run."""
    try:
        # Determine hive
        hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE

        # Read the current value first
        key = winreg.OpenKey(hive, registry_path, 0, winreg.KEY_READ)
        value, vtype = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)

        # Store in backup: "HIVE|REGPATH|EXEPATH"
        backup_value = f"{hive_name}|{registry_path}|{value}"
        bkey = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, BACKUP_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(bkey, name, 0, winreg.REG_SZ, backup_value)
        winreg.CloseKey(bkey)

        # Remove from startup
        key = winreg.OpenKey(hive, registry_path, 0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, name)
        winreg.CloseKey(key)

        logger.info(f"Disabled startup: {name}")
        return {"success": True, "name": name, "action": "disabled"}

    except Exception as e:
        logger.error(f"Error disabling {name}: {e}")
        return {"success": False, "name": name, "error": str(e)}


def enable_startup(name):
    """Re-enable a disabled startup program from backup."""
    try:
        # Read from backup
        bkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, BACKUP_KEY, 0,
                              winreg.KEY_READ | winreg.KEY_SET_VALUE)
        value, _ = winreg.QueryValueEx(bkey, name)
        parts = value.split("|", 2)

        if len(parts) != 3:
            winreg.CloseKey(bkey)
            return {"success": False, "error": "Invalid backup data"}

        hive_name, reg_path, exe_path = parts
        hive = winreg.HKEY_CURRENT_USER if hive_name == "HKCU" else winreg.HKEY_LOCAL_MACHINE

        # Restore to startup
        key = winreg.CreateKeyEx(hive, reg_path, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)

        # Remove from backup
        winreg.DeleteValue(bkey, name)
        winreg.CloseKey(bkey)

        logger.info(f"Enabled startup: {name}")
        return {"success": True, "name": name, "action": "enabled"}

    except Exception as e:
        logger.error(f"Error enabling {name}: {e}")
        return {"success": False, "name": name, "error": str(e)}


def get_boot_rating(programs=None):
    """Calculate boot speed rating based on startup count."""
    if programs is None:
        programs = get_startup_programs()

    enabled = sum(1 for p in programs if p["enabled"])

    if enabled <= 3:
        return {"rating": "Fast", "rating_ar": "سريع", "color": "#6ee7b7",
                "enabled_count": enabled, "total": len(programs)}
    elif enabled <= 7:
        return {"rating": "Moderate", "rating_ar": "متوسط", "color": "#fcd34d",
                "enabled_count": enabled, "total": len(programs)}
    else:
        return {"rating": "Slow", "rating_ar": "بطيء", "color": "#fca5a5",
                "enabled_count": enabled, "total": len(programs)}


def get_startup_info():
    """Get startup programs with boot rating."""
    programs = get_startup_programs()
    rating = get_boot_rating(programs)
    return {
        "programs": programs,
        "rating": rating,
    }
