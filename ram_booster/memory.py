"""
memory.py - Core memory management and cleaning operations.
Uses Windows APIs via ctypes for deep memory cleaning.
"""

import ctypes
import ctypes.wintypes as wintypes
import logging
import os
import subprocess
from dataclasses import dataclass
from typing import Optional

import psutil

logger = logging.getLogger("RamBooster.memory")

# ─────────────────────────────────────────────
# Windows API Constants
# ─────────────────────────────────────────────
SE_PRIVILEGE_ENABLED = 0x00000002
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
PROCESS_ALL_ACCESS = 0x1F0FFF
SystemMemoryListInformation = 80  # SYSTEM_INFORMATION_CLASS

# Memory purge commands for NtSetSystemInformation
MemoryPurgeStandbyList = 4
MemoryPurgeLowPriorityStandbyList = 5
MemoryPurgeModifiedList = 3


@dataclass
class MemoryInfo:
    """Snapshot of current system memory state."""
    total: int          # Total physical RAM in bytes
    available: int      # Available RAM in bytes
    used: int           # Used RAM in bytes
    percent: float      # Usage percentage (0-100)
    total_gb: float     # Total in GB
    available_gb: float # Available in GB
    used_gb: float      # Used in GB
    cached: float       # Cached memory in GB


def get_memory_info() -> MemoryInfo:
    """Get current system memory information."""
    mem = psutil.virtual_memory()
    return MemoryInfo(
        total=mem.total,
        available=mem.available,
        used=mem.used,
        percent=mem.percent,
        total_gb=round(mem.total / (1024 ** 3), 2),
        available_gb=round(mem.available / (1024 ** 3), 2),
        used_gb=round(mem.used / (1024 ** 3), 2),
        cached=round(getattr(mem, 'cached', 0) / (1024 ** 3), 2),
    )


def _enable_privilege(privilege_name: str) -> bool:
    """Enable a Windows privilege for the current process token."""
    try:
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32

        # Token privilege structure
        class LUID(ctypes.Structure):
            _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

        class LUID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

        class TOKEN_PRIVILEGES(ctypes.Structure):
            _fields_ = [
                ("PrivilegeCount", wintypes.DWORD),
                ("Privileges", LUID_AND_ATTRIBUTES * 1),
            ]

        # Declare function signatures for proper ctypes interop
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        kernel32.GetCurrentProcess.argtypes = []

        advapi32.OpenProcessToken.restype = wintypes.BOOL
        advapi32.OpenProcessToken.argtypes = [
            wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)
        ]

        advapi32.LookupPrivilegeValueW.restype = wintypes.BOOL
        advapi32.LookupPrivilegeValueW.argtypes = [
            wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.POINTER(LUID)
        ]

        advapi32.AdjustTokenPrivileges.restype = wintypes.BOOL
        advapi32.AdjustTokenPrivileges.argtypes = [
            wintypes.HANDLE, wintypes.BOOL, ctypes.POINTER(TOKEN_PRIVILEGES),
            wintypes.DWORD, ctypes.c_void_p, ctypes.c_void_p
        ]

        kernel32.CloseHandle.restype = wintypes.BOOL
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

        # Open process token
        h_token = wintypes.HANDLE()
        h_process = kernel32.GetCurrentProcess()
        if not advapi32.OpenProcessToken(
            h_process, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(h_token)
        ):
            logger.warning(f"Failed to open process token for privilege: {privilege_name}")
            return False

        # Lookup privilege value
        luid = LUID()
        if not advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
            kernel32.CloseHandle(h_token)
            logger.warning(f"Failed to lookup privilege: {privilege_name}")
            return False

        # Adjust token privileges
        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

        result = advapi32.AdjustTokenPrivileges(
            h_token, False, ctypes.byref(tp), 0, None, None
        )

        # Check GetLastError - AdjustTokenPrivileges returns True even on partial failure
        error = ctypes.GetLastError()
        kernel32.CloseHandle(h_token)

        if not result:
            logger.warning(f"AdjustTokenPrivileges failed for: {privilege_name}")
            return False

        if error == 0:
            logger.info(f"Privilege enabled: {privilege_name}")
            return True
        else:
            logger.warning(f"Privilege {privilege_name} - partial result (error={error})")
            return True  # Still proceed, may work

    except Exception as e:
        logger.error(f"Error enabling privilege {privilege_name}: {e}")
        return False


def clear_standby_list() -> bool:
    """
    Clear the Windows Standby List using NtSetSystemInformation.
    Requires administrator privileges.
    """
    try:
        # Enable required privileges
        _enable_privilege("SeProfileSingleProcessPrivilege")
        _enable_privilege("SeIncreaseQuotaPrivilege")

        ntdll = ctypes.windll.ntdll

        # Purge standby list
        command = ctypes.c_int(MemoryPurgeStandbyList)
        status = ntdll.NtSetSystemInformation(
            SystemMemoryListInformation,
            ctypes.byref(command),
            ctypes.sizeof(command),
        )

        if status == 0:
            logger.info("Standby list cleared successfully (NTSTATUS=0)")
            return True
        else:
            logger.warning(f"NtSetSystemInformation returned NTSTATUS: {hex(status & 0xFFFFFFFF)}")
            return False

    except Exception as e:
        logger.error(f"Error clearing standby list: {e}")
        return False


def clear_low_priority_standby() -> bool:
    """Clear only the low-priority standby list (less aggressive)."""
    try:
        _enable_privilege("SeProfileSingleProcessPrivilege")
        _enable_privilege("SeIncreaseQuotaPrivilege")

        ntdll = ctypes.windll.ntdll
        command = ctypes.c_int(MemoryPurgeLowPriorityStandbyList)
        status = ntdll.NtSetSystemInformation(
            SystemMemoryListInformation,
            ctypes.byref(command),
            ctypes.sizeof(command),
        )
        return status == 0
    except Exception as e:
        logger.error(f"Error clearing low priority standby: {e}")
        return False


def clear_modified_page_list() -> bool:
    """Flush modified page list to disk."""
    try:
        _enable_privilege("SeProfileSingleProcessPrivilege")
        _enable_privilege("SeIncreaseQuotaPrivilege")

        ntdll = ctypes.windll.ntdll
        command = ctypes.c_int(MemoryPurgeModifiedList)
        status = ntdll.NtSetSystemInformation(
            SystemMemoryListInformation,
            ctypes.byref(command),
            ctypes.sizeof(command),
        )
        return status == 0
    except Exception as e:
        logger.error(f"Error clearing modified page list: {e}")
        return False


def trim_processes_working_sets() -> int:
    """
    Reduce the working set of all accessible processes.
    Returns the number of processes trimmed.
    """
    trimmed = 0
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi

    # Protected system processes to skip
    protected = {
        "system", "smss.exe", "csrss.exe", "wininit.exe",
        "services.exe", "lsass.exe", "svchost.exe", "dwm.exe",
        "winlogon.exe", "explorer.exe", "registry",
    }

    current_pid = os.getpid()

    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            name = (proc.info['name'] or "").lower()

            # Skip protected processes and self
            if pid <= 4 or pid == current_pid or name in protected:
                continue

            # Open process handle
            handle = kernel32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
            if handle:
                # EmptyWorkingSet is equivalent to SetProcessWorkingSetSizeEx(-1, -1)
                result = psapi.EmptyWorkingSet(handle)
                if result:
                    trimmed += 1
                kernel32.CloseHandle(handle)

        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
        except Exception:
            continue

    logger.info(f"Trimmed working sets of {trimmed} processes")
    return trimmed


def flush_system_file_cache() -> bool:
    """
    Attempt to flush system file cache.
    Uses SetSystemFileCacheSize with minimum values.
    """
    try:
        _enable_privilege("SeIncreaseQuotaPrivilege")

        kernel32 = ctypes.windll.kernel32

        # SetSystemFileCacheSize(MinSize, MaxSize, Flags)
        # Setting both to -1 with flag 0 resets to defaults
        SIZE_T = ctypes.c_size_t
        result = kernel32.SetSystemFileCacheSize(
            SIZE_T(0xFFFFFFFFFFFFFFFF),  # -1
            SIZE_T(0xFFFFFFFFFFFFFFFF),  # -1
            ctypes.c_int(0),
        )

        if result:
            logger.info("System file cache flushed successfully")
            # Restore defaults
            kernel32.SetSystemFileCacheSize(
                SIZE_T(0), SIZE_T(0), ctypes.c_int(0)
            )
        return bool(result)

    except Exception as e:
        logger.error(f"Error flushing file cache: {e}")
        return False


def smart_clean() -> dict:
    """
    Perform a comprehensive memory cleaning operation.
    Returns a report of what was cleaned.
    """
    before = get_memory_info()
    report = {
        "before_used_gb": before.used_gb,
        "before_percent": before.percent,
        "standby_cleared": False,
        "modified_flushed": False,
        "cache_flushed": False,
        "processes_trimmed": 0,
        "freed_mb": 0,
    }

    # Step 1: Trim process working sets
    report["processes_trimmed"] = trim_processes_working_sets()

    # Step 2: Clear standby list
    report["standby_cleared"] = clear_standby_list()

    # Step 3: Flush modified pages
    report["modified_flushed"] = clear_modified_page_list()

    # Step 4: Flush file cache
    report["cache_flushed"] = flush_system_file_cache()

    # Calculate freed memory
    after = get_memory_info()
    freed_bytes = after.available - before.available
    report["freed_mb"] = max(0, round(freed_bytes / (1024 ** 2), 1))
    report["after_used_gb"] = after.used_gb
    report["after_percent"] = after.percent

    logger.info(f"Smart clean completed. Freed: {report['freed_mb']} MB")
    return report


def get_top_memory_processes(count: int = 15) -> list[dict]:
    """Get the top N processes by memory usage."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent', 'status']):
        try:
            info = proc.info
            if info['memory_info'] is None:
                continue
            mem_mb = info['memory_info'].rss / (1024 ** 2)
            if mem_mb < 1:  # Skip processes using less than 1 MB
                continue
            processes.append({
                'pid': info['pid'],
                'name': info['name'] or 'Unknown',
                'memory_mb': round(mem_mb, 1),
                'memory_percent': round(info['memory_percent'] or 0, 1),
                'status': info['status'],
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sort by memory usage descending
    processes.sort(key=lambda x: x['memory_mb'], reverse=True)
    return processes[:count]


def kill_process(pid: int) -> bool:
    """Kill a specific process by PID."""
    try:
        proc = psutil.Process(pid)
        proc.terminate()
        proc.wait(timeout=3)
        logger.info(f"Process {pid} ({proc.name()}) terminated")
        return True
    except Exception as e:
        logger.error(f"Failed to kill process {pid}: {e}")
        return False


def is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_admin_restart() -> None:
    """Restart the application with administrator privileges."""
    import sys
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    sys.exit(0)
