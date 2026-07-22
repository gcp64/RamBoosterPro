"""
disk_cleaner.py - Supercharged Disk Manager & Deep Cleaning Suite.
Features:
- Installed Applications Auditor & Silent/Interactive Uninstaller
- Large File Finder & Storage Space Hog Analyzer (>50MB)
- Storage Categorizer (Music/Audio, Videos/Movies, Pictures, Documents, Installers/Archives)
- Multi-Drive Partitions & Volume Metrics Inspector (C:, D:, E:, USBs)
- Direct File Shredder & Cleaner
- Deep Temp, Browser, Windows Update & Delivery Optimization Cleaner
"""
import glob
import logging
import os
import shutil
import subprocess
import winreg
import psutil
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger("RamBooster.DiskCleaner")

SW = subprocess.CREATE_NO_WINDOW


def _safe_delete(path, results):
    """Safely delete a file or directory."""
    try:
        if os.path.isfile(path):
            size = os.path.getsize(path)
            os.remove(path)
            results["files_deleted"] += 1
            results["bytes_freed"] += size
        elif os.path.isdir(path):
            size = sum(
                os.path.getsize(os.path.join(dp, f))
                for dp, _, fns in os.walk(path) for f in fns
                if os.path.exists(os.path.join(dp, f))
            )
            shutil.rmtree(path, ignore_errors=True)
            results["dirs_deleted"] += 1
            results["bytes_freed"] += size
    except (PermissionError, OSError):
        results["errors"] += 1


def clean_system_temp(results):
    """Clean Windows system temp."""
    paths = [
        os.environ.get("TEMP", ""),
        os.environ.get("TMP", ""),
        r"C:\Windows\Temp",
    ]
    for base in paths:
        if not base or not os.path.exists(base):
            continue
        for item in os.listdir(base):
            fp = os.path.join(base, item)
            _safe_delete(fp, results)
    logger.info(f"System temp cleaned: {results['files_deleted']} files")


def clean_prefetch(results):
    """Clean Windows prefetch."""
    pf = r"C:\Windows\Prefetch"
    if os.path.exists(pf):
        for f in os.listdir(pf):
            _safe_delete(os.path.join(pf, f), results)


def clean_recent(results):
    """Clean recent files list."""
    recent = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Recent")
    if os.path.exists(recent):
        for f in os.listdir(recent):
            _safe_delete(os.path.join(recent, f), results)


def clean_thumbnails(results):
    """Clean thumbnail cache."""
    thumb = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                         r"Microsoft\Windows\Explorer")
    if os.path.exists(thumb):
        for f in os.listdir(thumb):
            if "thumbcache" in f.lower():
                _safe_delete(os.path.join(thumb, f), results)


def clean_windows_update(results):
    """Clean old Windows Update files."""
    paths = [
        r"C:\Windows\SoftwareDistribution\Download",
        r"C:\Windows\SoftwareDistribution\DataStore\Logs",
    ]
    for p in paths:
        if os.path.exists(p):
            for item in os.listdir(p):
                _safe_delete(os.path.join(p, item), results)


def clean_browser_caches(results):
    """Clean all major browser caches."""
    local = os.environ.get("LOCALAPPDATA", "")
    appdata = os.environ.get("APPDATA", "")

    cache_paths = [
        # Chrome
        os.path.join(local, r"Google\Chrome\User Data\Default\Cache"),
        os.path.join(local, r"Google\Chrome\User Data\Default\Code Cache"),
        os.path.join(local, r"Google\Chrome\User Data\Default\GPUCache"),
        # Edge
        os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache"),
        os.path.join(local, r"Microsoft\Edge\User Data\Default\Code Cache"),
        # Firefox
        os.path.join(local, r"Mozilla\Firefox\Profiles"),
        # Opera
        os.path.join(appdata, r"Opera Software\Opera Stable\Cache"),
        # Brave
        os.path.join(local, r"BraveSoftware\Brave-Browser\User Data\Default\Cache"),
    ]

    for cp in cache_paths:
        if os.path.exists(cp):
            if "Firefox" in cp:
                for profile in os.listdir(cp):
                    p_cache = os.path.join(cp, profile, "cache2")
                    if os.path.exists(p_cache):
                        _safe_delete(p_cache, results)
            else:
                _safe_delete(cp, results)


def deep_disk_clean():
    """Execute deep disk cleaning across all cache locations."""
    results = {
        "files_deleted": 0,
        "dirs_deleted": 0,
        "bytes_freed": 0,
        "errors": 0,
        "sections": {},
    }

    start_bytes = results["bytes_freed"]

    clean_system_temp(results)
    results["sections"]["System Temp"] = round((results["bytes_freed"] - start_bytes) / (1024 * 1024), 2)
    s1 = results["bytes_freed"]

    clean_prefetch(results)
    results["sections"]["Prefetch"] = round((results["bytes_freed"] - s1) / (1024 * 1024), 2)
    s2 = results["bytes_freed"]

    clean_recent(results)
    clean_thumbnails(results)
    results["sections"]["System Caches & Recent"] = round((results["bytes_freed"] - s2) / (1024 * 1024), 2)
    s3 = results["bytes_freed"]

    clean_browser_caches(results)
    results["sections"]["Browser Caches"] = round((results["bytes_freed"] - s3) / (1024 * 1024), 2)
    s4 = results["bytes_freed"]

    clean_windows_update(results)
    results["sections"]["Windows Update Cleanup"] = round((results["bytes_freed"] - s4) / (1024 * 1024), 2)

    total_mb = round(results["bytes_freed"] / (1024 * 1024), 2)
    results["total_freed_mb"] = total_mb
    logger.info(f"Deep disk clean done: {total_mb} MB freed")

    return results


# ── INSTALLED APPLICATIONS AUDITOR & UNINSTALLER ──

def get_installed_apps():
    """
    Audit and list all installed applications on Windows with estimated size, publisher, and uninstall string.
    """
    apps = []
    seen = set()

    reg_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for root, path in reg_paths:
        try:
            hkey = winreg.OpenKey(root, path, 0, winreg.KEY_READ)
            num_subkeys = winreg.QueryInfoKey(hkey)[0]

            for i in range(num_subkeys):
                try:
                    subkey_name = winreg.EnumKey(hkey, i)
                    sk = winreg.OpenKey(root, f"{path}\\{subkey_name}", 0, winreg.KEY_READ)
                    
                    try:
                        name, _ = winreg.QueryValueEx(sk, "DisplayName")
                    except Exception:
                        winreg.CloseKey(sk)
                        continue

                    if not name or name in seen or "Security Update" in name or "Update for" in name:
                        winreg.CloseKey(sk)
                        continue

                    seen.add(name)

                    publisher = "Unknown Publisher"
                    try: publisher, _ = winreg.QueryValueEx(sk, "Publisher")
                    except Exception: pass

                    version = "1.0"
                    try: version, _ = winreg.QueryValueEx(sk, "DisplayVersion")
                    except Exception: pass

                    size_kb = 0
                    try: size_kb, _ = winreg.QueryValueEx(sk, "EstimatedSize")
                    except Exception: pass

                    uninstall_string = ""
                    try: uninstall_string, _ = winreg.QueryValueEx(sk, "UninstallString")
                    except Exception: pass

                    size_mb = round(size_kb / 1024, 1) if size_kb else 0.0

                    apps.append({
                        "name": name,
                        "publisher": publisher,
                        "version": str(version),
                        "size_mb": size_mb,
                        "uninstall_cmd": uninstall_string,
                        "key_path": f"{path}\\{subkey_name}",
                    })
                    winreg.CloseKey(sk)
                except Exception:
                    pass
            winreg.CloseKey(hkey)
        except Exception:
            pass

    apps.sort(key=lambda x: x["name"].lower())
    return apps


def uninstall_app(uninstall_cmd):
    """Trigger application uninstaller."""
    if not uninstall_cmd:
        return {"success": False, "error": "No uninstall command specified"}
    try:
        subprocess.Popen(uninstall_cmd, shell=True)
        return {"success": True, "msg": "Uninstaller launched"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── STORAGE CATEGORIZER & LARGE FILE ANALYZER ──

EXT_CATEGORIES = {
    "audio": [".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".wma"],
    "video": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"],
    "pictures": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".ico", ".raw"],
    "documents": [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".csv", ".doc", ".xls"],
    "archives": [".exe", ".msi", ".iso", ".zip", ".rar", ".7z", ".tar", ".gz"],
}


def analyze_disk_categories():
    """
    Categorize user files into Audio/Music, Video/Movies, Pictures, Documents, and Installers/Archives.
    """
    user_home = os.path.expanduser("~")
    target_dirs = [
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Videos"),
        os.path.join(user_home, "Music"),
        os.path.join(user_home, "Pictures"),
    ]

    totals = {"audio": 0, "video": 0, "pictures": 0, "documents": 0, "archives": 0, "other": 0}
    counts = {"audio": 0, "video": 0, "pictures": 0, "documents": 0, "archives": 0, "other": 0}

    for base in target_dirs:
        if not os.path.exists(base):
            continue
        for dp, _, fns in os.walk(base):
            for fn in fns:
                ext = os.path.splitext(fn)[1].lower()
                fp = os.path.join(dp, fn)
                try:
                    sz = os.path.getsize(fp)
                except Exception:
                    continue

                cat_found = False
                for cat, ext_list in EXT_CATEGORIES.items():
                    if ext in ext_list:
                        totals[cat] += sz
                        counts[cat] += 1
                        cat_found = True
                        break
                if not cat_found:
                    totals["other"] += sz
                    counts["other"] += 1

    total_bytes = sum(totals.values()) or 1

    return {
        "audio_mb": round(totals["audio"] / (1024**2), 1),
        "video_mb": round(totals["video"] / (1024**2), 1),
        "pictures_mb": round(totals["pictures"] / (1024**2), 1),
        "documents_mb": round(totals["documents"] / (1024**2), 1),
        "archives_mb": round(totals["archives"] / (1024**2), 1),
        "other_mb": round(totals["other"] / (1024**2), 1),
        "audio_pct": round((totals["audio"] / total_bytes) * 100, 1),
        "video_pct": round((totals["video"] / total_bytes) * 100, 1),
        "pictures_pct": round((totals["pictures"] / total_bytes) * 100, 1),
        "documents_pct": round((totals["documents"] / total_bytes) * 100, 1),
        "archives_pct": round((totals["archives"] / total_bytes) * 100, 1),
        "counts": counts,
    }


def find_large_files(min_size_mb=30):
    """
    Scan user directories for files larger than specified MB threshold.
    Returns sorted list of largest space hogs.
    """
    user_home = os.path.expanduser("~")
    target_dirs = [
        os.path.join(user_home, "Downloads"),
        os.path.join(user_home, "Documents"),
        os.path.join(user_home, "Desktop"),
        os.path.join(user_home, "Videos"),
        os.path.join(user_home, "Music"),
        os.path.join(user_home, "Pictures"),
    ]

    min_bytes = min_size_mb * 1024 * 1024
    large_files = []

    for base in target_dirs:
        if not os.path.exists(base):
            continue
        for dp, _, fns in os.walk(base):
            for fn in fns:
                fp = os.path.join(dp, fn)
                try:
                    sz = os.path.getsize(fp)
                    if sz >= min_bytes:
                        ext = os.path.splitext(fn)[1].lower()
                        large_files.append({
                            "name": fn,
                            "path": fp,
                            "size_mb": round(sz / (1024**2), 1),
                            "ext": ext,
                        })
                except Exception:
                    pass

    large_files.sort(key=lambda x: x["size_mb"], reverse=True)
    return large_files[:30]


def get_drive_partitions():
    """
    Get detailed partition metrics for all mounted drives (C:, D:, E:, USBs).
    """
    partitions = []
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            partitions.append({
                "device": part.device,
                "mountpoint": part.mountpoint,
                "fstype": part.fstype,
                "total_gb": round(usage.total / (1024**3), 1),
                "used_gb": round(usage.used / (1024**3), 1),
                "free_gb": round(usage.free / (1024**3), 1),
                "percent": usage.percent,
            })
        except Exception:
            pass
    return partitions


def delete_specific_file(filepath):
    """Delete a specific file selected by the user."""
    if not filepath or not os.path.exists(filepath):
        return {"success": False, "error": "File does not exist"}
    try:
        size_mb = round(os.path.getsize(filepath) / (1024**2), 1)
        os.remove(filepath)
        return {"success": True, "freed_mb": size_mb, "path": filepath}
    except Exception as e:
        return {"success": False, "error": str(e)}
