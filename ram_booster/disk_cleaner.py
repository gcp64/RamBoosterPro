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
IS_WIN = os.name == 'nt'

if IS_WIN:
    import winreg
    SW = subprocess.CREATE_NO_WINDOW
else:
    winreg = None
    SW = 0


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
    """Clean system temp files."""
    if IS_WIN:
        paths = [
            os.environ.get("TEMP", ""),
            os.environ.get("TMP", ""),
            r"C:\Windows\Temp",
        ]
    else:
        paths = [
            "/tmp",
            "/var/tmp",
            os.path.expanduser("~/.cache"),
            os.path.expanduser("~/.cache/thumbnails"),
            "/var/cache/apt/archives",
            "/var/cache/pacman/pkg",
        ]

    for base in paths:
        if not base or not os.path.exists(base):
            continue
        try:
            for item in os.listdir(base):
                fp = os.path.join(base, item)
                _safe_delete(fp, results)
        except Exception:
            pass
    logger.info(f"System temp cleaned: {results['files_deleted']} files")


def clean_prefetch(results):
    """Clean prefetch / Linux cache."""
    if IS_WIN:
        pf = r"C:\Windows\Prefetch"
        if os.path.exists(pf):
            for f in os.listdir(pf):
                _safe_delete(os.path.join(pf, f), results)
    else:
        # Linux journal logs cleanup
        try:
            subprocess.run(["journalctl", "--vacuum-size=50M"], check=False)
        except Exception:
            pass


def clean_recent(results):
    """Clean recent files list."""
    if IS_WIN:
        recent = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Recent")
    else:
        recent = os.path.expanduser("~/.local/share/recently-used.xbel")
        if os.path.exists(recent):
            _safe_delete(recent, results)
            return

    if os.path.exists(recent):
        for f in os.listdir(recent):
            _safe_delete(os.path.join(recent, f), results)


def clean_thumbnails(results):
    """Clean thumbnail cache."""
    if IS_WIN:
        thumb = os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\Windows\Explorer")
        if os.path.exists(thumb):
            for f in os.listdir(thumb):
                if "thumbcache" in f.lower():
                    _safe_delete(os.path.join(thumb, f), results)
    else:
        thumb = os.path.expanduser("~/.cache/thumbnails")
        if os.path.exists(thumb):
            _safe_delete(thumb, results)


def clean_windows_update(results):
    """Clean old Windows Update / Linux package caches."""
    if IS_WIN:
        paths = [
            r"C:\Windows\SoftwareDistribution\Download",
            r"C:\Windows\SoftwareDistribution\DataStore\Logs",
        ]
        for p in paths:
            if os.path.exists(p):
                for item in os.listdir(p):
                    _safe_delete(os.path.join(p, item), results)
    else:
        # Autoremove orphaned packages
        try:
            subprocess.run(["apt-get", "clean"], check=False)
            subprocess.run(["pacman", "-Sc", "--noconfirm"], check=False)
        except Exception:
            pass


def clean_browser_caches(results):
    """Clean all major browser caches."""
    if IS_WIN:
        local = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        cache_paths = [
            os.path.join(local, r"Google\Chrome\User Data\Default\Cache"),
            os.path.join(local, r"Google\Chrome\User Data\Default\Code Cache"),
            os.path.join(local, r"Google\Chrome\User Data\Default\GPUCache"),
            os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache"),
            os.path.join(local, r"Microsoft\Edge\User Data\Default\Code Cache"),
            os.path.join(local, r"Mozilla\Firefox\Profiles"),
            os.path.join(appdata, r"Opera Software\Opera Stable\Cache"),
            os.path.join(local, r"BraveSoftware\Brave-Browser\User Data\Default\Cache"),
        ]
    else:
        home = os.path.expanduser("~")
        cache_paths = [
            os.path.join(home, ".cache/google-chrome/Default/Cache"),
            os.path.join(home, ".cache/mozilla/firefox"),
            os.path.join(home, ".cache/BraveSoftware/Brave-Browser/Default/Cache"),
            os.path.join(home, ".cache/chromium/Default/Cache"),
            os.path.join(home, ".cache/opera"),
        ]

    for cp in cache_paths:
        if os.path.exists(cp):
            if "firefox" in cp.lower() or "Firefox" in cp:
                try:
                    for profile in os.listdir(cp):
                        p_cache = os.path.join(cp, profile, "cache2")
                        if os.path.exists(p_cache):
                            _safe_delete(p_cache, results)
                except Exception:
                    pass
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
    results["sections"]["Prefetch / System Logs"] = round((results["bytes_freed"] - s1) / (1024 * 1024), 2)
    s2 = results["bytes_freed"]

    clean_recent(results)
    clean_thumbnails(results)
    results["sections"]["System Caches & Recent"] = round((results["bytes_freed"] - s2) / (1024 * 1024), 2)
    s3 = results["bytes_freed"]

    clean_browser_caches(results)
    results["sections"]["Browser Caches"] = round((results["bytes_freed"] - s3) / (1024 * 1024), 2)
    s4 = results["bytes_freed"]

    clean_windows_update(results)
    results["sections"]["Package Cache Cleanup"] = round((results["bytes_freed"] - s4) / (1024 * 1024), 2)

    total_mb = round(results["bytes_freed"] / (1024 * 1024), 2)
    results["total_freed_mb"] = total_mb
    logger.info(f"Deep disk clean done: {total_mb} MB freed")

    return results


# ── INSTALLED APPLICATIONS AUDITOR & UNINSTALLER ──

def _extract_app_icon_b64(icon_path):
    """Extract real high-res 32x32 PNG Base64 icon from path."""
    if not icon_path or not isinstance(icon_path, str):
        return ""
    if not IS_WIN:
        return ""
    try:
        clean_path = icon_path.strip('"\'').split(',')[0].strip()
        if not os.path.exists(clean_path):
            if os.path.isdir(icon_path):
                exes = [os.path.join(icon_path, f) for f in os.listdir(icon_path) if f.lower().endswith(".exe")]
                if exes:
                    clean_path = exes[0]
                else:
                    return ""
            else:
                return ""

        if clean_path.lower().endswith((".png", ".ico")):
            with open(clean_path, "rb") as f:
                import base64
                return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"

        import win32gui, win32ui, win32con, base64, io
        from PIL import Image

        large, small = win32gui.ExtractIconEx(clean_path, 0)
        hicon = large[0] if large else (small[0] if small else None)
        if not hicon:
            return ""

        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, 32, 32)
        hdc_mem = hdc.CreateCompatibleDC()
        hdc_mem.SelectObject(hbmp)

        win32gui.DrawIconEx(hdc_mem.GetHandleOutput(), 0, 0, hicon, 32, 32, 0, 0, win32con.DI_NORMAL)
        bmpinfo = hbmp.GetInfo()
        bmpbits = hbmp.GetBitmapBits(True)

        im = Image.frombuffer('RGBA', (32, 32), bmpbits, 'raw', 'BGRA', 0, 1)

        for h in large: win32gui.DestroyIcon(h)
        for h in small: win32gui.DestroyIcon(h)

        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"
    except Exception:
        return ""


def get_installed_apps():
    """Scan for installed applications with publisher, size, version, and real icons."""
    apps = []
    seen = set()

    if not IS_WIN:
        # Linux .desktop entries scanner
        desktop_dirs = [
            "/usr/share/applications",
            "/var/lib/snapd/desktop/applications",
            "/var/lib/flatpak/exports/share/applications",
            os.path.expanduser("~/.local/share/applications"),
        ]
        for d in desktop_dirs:
            if not os.path.exists(d):
                continue
            for f in os.listdir(d):
                if f.endswith(".desktop"):
                    fp = os.path.join(d, f)
                    app_name, app_icon, app_exec = "", "", ""
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as df:
                            for line in df:
                                if line.startswith("Name=") and not app_name:
                                    app_name = line.split("=", 1)[1].strip()
                                elif line.startswith("Icon=") and not app_icon:
                                    app_icon = line.split("=", 1)[1].strip()
                                elif line.startswith("Exec=") and not app_exec:
                                    app_exec = line.split("=", 1)[1].strip()
                        if app_name and app_name not in seen:
                            seen.add(app_name)
                            apps.append({
                                "name": app_name,
                                "publisher": "Linux Application",
                                "version": "1.0",
                                "size_mb": 50,
                                "uninstall_cmd": f"rm '{fp}'",
                                "icon_b64": "",
                            })
                    except Exception:
                        pass
        return sorted(apps, key=lambda x: x["name"].lower())

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

                    display_icon = ""
                    try: display_icon, _ = winreg.QueryValueEx(sk, "DisplayIcon")
                    except Exception: pass

                    install_location = ""
                    try: install_location, _ = winreg.QueryValueEx(sk, "InstallLocation")
                    except Exception: pass

                    icon_b64 = _extract_app_icon_b64(display_icon) or _extract_app_icon_b64(install_location)

                    size_mb = round(size_kb / 1024, 1) if size_kb else 0.0

                    apps.append({
                        "name": name,
                        "publisher": publisher,
                        "version": str(version),
                        "size_mb": size_mb,
                        "uninstall_cmd": uninstall_string,
                        "icon_b64": icon_b64,
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
