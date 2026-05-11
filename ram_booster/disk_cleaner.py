"""
disk_cleaner.py - Deep Disk Cleaning Engine.
Cleans temp files, browser caches, Windows update leftovers, and more.
"""
import glob
import logging
import os
import shutil
import subprocess

logger = logging.getLogger("RamBooster.DiskCleaner")


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
        os.path.join(local, r"Google\Chrome\User Data\Default\Service Worker\CacheStorage"),
        os.path.join(local, r"Google\Chrome\User Data\ShaderCache"),
        # Edge
        os.path.join(local, r"Microsoft\Edge\User Data\Default\Cache"),
        os.path.join(local, r"Microsoft\Edge\User Data\Default\Code Cache"),
        os.path.join(local, r"Microsoft\Edge\User Data\Default\GPUCache"),
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
                # Firefox has profile subdirs
                for profile in os.listdir(cp):
                    ff_cache = os.path.join(cp, profile, "cache2")
                    if os.path.exists(ff_cache):
                        for item in os.listdir(ff_cache):
                            _safe_delete(os.path.join(ff_cache, item), results)
            else:
                for item in os.listdir(cp):
                    _safe_delete(os.path.join(cp, item), results)

    logger.info(f"Browser caches cleaned")


def clean_logs(results):
    """Clean old log files."""
    log_dirs = [
        r"C:\Windows\Logs",
        r"C:\Windows\Debug",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "CrashDumps"),
    ]
    for ld in log_dirs:
        if os.path.exists(ld):
            for item in os.listdir(ld):
                fp = os.path.join(ld, item)
                if os.path.isfile(fp):
                    _safe_delete(fp, results)


def clean_recycle_bin(results):
    """Empty recycle bin."""
    try:
        import ctypes
        ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 0x07)
        logger.info("Recycle bin emptied")
    except Exception as e:
        logger.warning(f"Recycle bin: {e}")


def deep_disk_clean():
    """Run all deep disk cleaning operations."""
    results = {
        "files_deleted": 0,
        "dirs_deleted": 0,
        "bytes_freed": 0,
        "errors": 0,
        "sections": {},
    }

    sections = [
        ("System Temp", clean_system_temp),
        ("Prefetch", clean_prefetch),
        ("Recent Files", clean_recent),
        ("Thumbnails", clean_thumbnails),
        ("Windows Update", clean_windows_update),
        ("Browser Caches", clean_browser_caches),
        ("System Logs", clean_logs),
        ("Recycle Bin", clean_recycle_bin),
    ]

    for name, func in sections:
        before = results["bytes_freed"]
        try:
            func(results)
        except Exception as e:
            logger.error(f"{name}: {e}")
        freed_section = results["bytes_freed"] - before
        results["sections"][name] = round(freed_section / (1024 * 1024), 1)

    results["total_freed_mb"] = round(results["bytes_freed"] / (1024 * 1024), 1)
    logger.info(
        f"Deep clean done: {results['files_deleted']} files, "
        f"{results['total_freed_mb']} MB freed"
    )
    return results
