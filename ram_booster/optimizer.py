"""
optimizer.py - System optimization operations.
Handles temp file cleaning, browser cache clearing, and system boost.
"""

import logging
import os
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger("RamBooster.optimizer")


@dataclass
class CleanupReport:
    """Report of a cleanup operation."""
    files_deleted: int = 0
    folders_deleted: int = 0
    bytes_freed: int = 0
    errors: int = 0
    paths_cleaned: list = field(default_factory=list)

    @property
    def freed_mb(self) -> float:
        return round(self.bytes_freed / (1024 ** 2), 1)

    @property
    def freed_gb(self) -> float:
        return round(self.bytes_freed / (1024 ** 3), 2)


def _safe_remove_file(filepath: str, report: CleanupReport) -> None:
    """Safely remove a single file."""
    try:
        size = os.path.getsize(filepath)
        os.remove(filepath)
        report.files_deleted += 1
        report.bytes_freed += size
    except PermissionError:
        report.errors += 1
    except FileNotFoundError:
        pass
    except Exception:
        report.errors += 1


def _safe_remove_dir(dirpath: str, report: CleanupReport) -> None:
    """Safely remove a directory and its contents."""
    try:
        total_size = 0
        file_count = 0
        for root, dirs, files in os.walk(dirpath):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total_size += os.path.getsize(fp)
                    file_count += 1
                except OSError:
                    pass

        shutil.rmtree(dirpath, ignore_errors=True)

        if not os.path.exists(dirpath):
            report.folders_deleted += 1
            report.files_deleted += file_count
            report.bytes_freed += total_size
    except Exception:
        report.errors += 1


def _clean_directory(dirpath: str, report: CleanupReport, max_age_hours: int = 0) -> None:
    """
    Clean all files and subdirectories in a directory.
    If max_age_hours > 0, only delete items older than that.
    """
    if not os.path.exists(dirpath):
        return

    now = time.time()
    cutoff = now - (max_age_hours * 3600) if max_age_hours > 0 else 0

    try:
        for item in os.listdir(dirpath):
            item_path = os.path.join(dirpath, item)
            try:
                # Check age if needed
                if cutoff > 0:
                    mtime = os.path.getmtime(item_path)
                    if mtime > cutoff:
                        continue

                if os.path.isfile(item_path) or os.path.islink(item_path):
                    _safe_remove_file(item_path, report)
                elif os.path.isdir(item_path):
                    _safe_remove_dir(item_path, report)

            except (PermissionError, OSError):
                report.errors += 1
                continue
    except PermissionError:
        report.errors += 1


def clean_windows_temp() -> CleanupReport:
    """Clean the Windows system temp directory."""
    report = CleanupReport()
    win_temp = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Temp")
    logger.info(f"Cleaning Windows Temp: {win_temp}")
    _clean_directory(win_temp, report)
    report.paths_cleaned.append(win_temp)
    return report


def clean_user_temp() -> CleanupReport:
    """Clean the current user's temp directory."""
    report = CleanupReport()
    user_temp = os.environ.get("TEMP", os.environ.get("TMP", ""))
    if user_temp and os.path.exists(user_temp):
        logger.info(f"Cleaning User Temp: {user_temp}")
        _clean_directory(user_temp, report)
        report.paths_cleaned.append(user_temp)
    return report


def clean_prefetch() -> CleanupReport:
    """Clean the Windows Prefetch directory (requires admin)."""
    report = CleanupReport()
    prefetch = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Prefetch")
    if os.path.exists(prefetch):
        logger.info(f"Cleaning Prefetch: {prefetch}")
        _clean_directory(prefetch, report)
        report.paths_cleaned.append(prefetch)
    return report


def clean_recent_files() -> CleanupReport:
    """Clean the Windows Recent files list."""
    report = CleanupReport()
    recent = os.path.join(os.environ.get("APPDATA", ""), "Microsoft", "Windows", "Recent")
    if os.path.exists(recent):
        logger.info(f"Cleaning Recent: {recent}")
        _clean_directory(recent, report)
        report.paths_cleaned.append(recent)
    return report


def clean_thumbnails() -> CleanupReport:
    """Clean the Windows thumbnail cache."""
    report = CleanupReport()
    local_app = os.environ.get("LOCALAPPDATA", "")
    thumb_cache = os.path.join(local_app, "Microsoft", "Windows", "Explorer")
    if os.path.exists(thumb_cache):
        for item in os.listdir(thumb_cache):
            if item.startswith("thumbcache_") or item.startswith("iconcache_"):
                fp = os.path.join(thumb_cache, item)
                _safe_remove_file(fp, report)
        report.paths_cleaned.append(thumb_cache)
    return report


def clean_windows_logs() -> CleanupReport:
    """Clean various Windows log files."""
    report = CleanupReport()
    log_dirs = [
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Logs"),
        os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Debug"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "CrashDumps"),
    ]
    for log_dir in log_dirs:
        if os.path.exists(log_dir):
            _clean_directory(log_dir, report, max_age_hours=24)
            report.paths_cleaned.append(log_dir)
    return report


def clean_dns_cache() -> bool:
    """Flush the DNS resolver cache."""
    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        success = result.returncode == 0
        logger.info(f"DNS cache flush: {'success' if success else 'failed'}")
        return success
    except Exception as e:
        logger.error(f"DNS flush error: {e}")
        return False


def system_boost() -> dict:
    """
    Perform a full system boost operation.
    Cleans temp files, logs, caches, and flushes DNS.
    Returns a comprehensive report.
    """
    logger.info("Starting system boost operation")
    total_report = CleanupReport()

    # Define all cleaning operations
    operations = [
        ("Windows Temp", clean_windows_temp),
        ("User Temp", clean_user_temp),
        ("Prefetch", clean_prefetch),
        ("Recent Files", clean_recent_files),
        ("Thumbnails", clean_thumbnails),
        ("Windows Logs", clean_windows_logs),
    ]

    details = []
    for name, func in operations:
        try:
            report = func()
            total_report.files_deleted += report.files_deleted
            total_report.folders_deleted += report.folders_deleted
            total_report.bytes_freed += report.bytes_freed
            total_report.errors += report.errors
            total_report.paths_cleaned.extend(report.paths_cleaned)
            details.append({
                "name": name,
                "files": report.files_deleted,
                "freed_mb": report.freed_mb,
            })
        except Exception as e:
            logger.error(f"Error in {name}: {e}")
            details.append({"name": name, "files": 0, "freed_mb": 0, "error": str(e)})

    # Flush DNS
    dns_ok = clean_dns_cache()

    result = {
        "total_files_deleted": total_report.files_deleted,
        "total_folders_deleted": total_report.folders_deleted,
        "total_freed_mb": total_report.freed_mb,
        "total_freed_gb": total_report.freed_gb,
        "total_errors": total_report.errors,
        "dns_flushed": dns_ok,
        "details": details,
        "paths_cleaned": len(total_report.paths_cleaned),
    }

    logger.info(
        f"System boost complete: {result['total_files_deleted']} files, "
        f"{result['total_freed_mb']} MB freed"
    )
    return result


def get_disk_usage(path: str = "C:\\") -> dict:
    """Get disk usage information."""
    try:
        usage = shutil.disk_usage(path)
        return {
            "total_gb": round(usage.total / (1024 ** 3), 1),
            "used_gb": round(usage.used / (1024 ** 3), 1),
            "free_gb": round(usage.free / (1024 ** 3), 1),
            "percent": round((usage.used / usage.total) * 100, 1),
        }
    except Exception:
        return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}
