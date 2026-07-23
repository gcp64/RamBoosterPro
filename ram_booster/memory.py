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

IS_WIN = os.name == 'nt'

if IS_WIN:
    import ctypes.wintypes as wintypes
else:
    wintypes = None


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
        cached=round(getattr(mem, 'cached', getattr(mem, 'buffers', 0)) / (1024 ** 3), 2),
    )


def _enable_privilege(privilege_name: str) -> bool:
    """Enable a Windows privilege for the current process token."""
    if not IS_WIN:
        return True
    try:
        advapi32 = ctypes.windll.advapi32
        kernel32 = ctypes.windll.kernel32

        class LUID(ctypes.Structure):
            _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

        class LUID_AND_ATTRIBUTES(ctypes.Structure):
            _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

        class TOKEN_PRIVILEGES(ctypes.Structure):
            _fields_ = [
                ("PrivilegeCount", wintypes.DWORD),
                ("Privileges", LUID_AND_ATTRIBUTES * 1),
            ]

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

        h_token = wintypes.HANDLE()
        h_process = kernel32.GetCurrentProcess()
        if not advapi32.OpenProcessToken(
            h_process, TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY, ctypes.byref(h_token)
        ):
            return False

        luid = LUID()
        if not advapi32.LookupPrivilegeValueW(None, privilege_name, ctypes.byref(luid)):
            kernel32.CloseHandle(h_token)
            return False

        tp = TOKEN_PRIVILEGES()
        tp.PrivilegeCount = 1
        tp.Privileges[0].Luid = luid
        tp.Privileges[0].Attributes = SE_PRIVILEGE_ENABLED

        result = advapi32.AdjustTokenPrivileges(
            h_token, False, ctypes.byref(tp), 0, None, None
        )
        error = ctypes.GetLastError()
        kernel32.CloseHandle(h_token)

        return bool(result)
    except Exception as e:
        logger.error(f"Error enabling privilege {privilege_name}: {e}")
        return False


def clear_standby_list() -> bool:
    """Clear Standby List on Windows or drop_caches on Linux."""
    if not IS_WIN:
        try:
            subprocess.run(["sync"], check=False)
            if is_admin():
                with open("/proc/sys/vm/drop_caches", "w") as f:
                    f.write("3\n")
            else:
                subprocess.run(["sudo", "sysctl", "vm.drop_caches=3"], check=False)
            return True
        except Exception as e:
            logger.error(f"Linux drop_caches error: {e}")
            return False

    try:
        _enable_privilege("SeProfileSingleProcessPrivilege")
        _enable_privilege("SeIncreaseQuotaPrivilege")
        ntdll = ctypes.windll.ntdll
        command = ctypes.c_int(MemoryPurgeStandbyList)
        status = ntdll.NtSetSystemInformation(
            SystemMemoryListInformation,
            ctypes.byref(command),
            ctypes.sizeof(command),
        )
        return status == 0
    except Exception as e:
        logger.error(f"Error clearing standby list: {e}")
        return False


def clear_low_priority_standby() -> bool:
    """Clear low priority standby list."""
    if not IS_WIN:
        return clear_standby_list()
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
    """Flush modified page list."""
    if not IS_WIN:
        try:
            subprocess.run(["sync"], check=False)
            return True
        except Exception:
            return False
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
    """Reduce working set of processes."""
    if not IS_WIN:
        # On Linux, run sync
        try:
            subprocess.run(["sync"], check=False)
        except Exception:
            pass
        return 0

    trimmed = 0
    kernel32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
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
            if pid <= 4 or pid == current_pid or name in protected:
                continue

            PROCESS_SET_QUOTA = 0x0100
            PROCESS_QUERY_INFORMATION = 0x0400
            handle = kernel32.OpenProcess(PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, pid)
            if handle:
                result = psapi.EmptyWorkingSet(handle)
                if not result:
                    SIZE_T = ctypes.c_size_t
                    kernel32.SetProcessWorkingSetSize.argtypes = [wintypes.HANDLE, SIZE_T, SIZE_T]
                    kernel32.SetProcessWorkingSetSize.restype = wintypes.BOOL
                    result = kernel32.SetProcessWorkingSetSize(handle, SIZE_T(-1), SIZE_T(-1))
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
    """Flush system file cache."""
    if not IS_WIN:
        try:
            subprocess.run(["sync"], check=False)
            return True
        except Exception:
            return False

    try:
        _enable_privilege("SeIncreaseQuotaPrivilege")
        kernel32 = ctypes.windll.kernel32
        SIZE_T = ctypes.c_size_t
        kernel32.SetSystemFileCacheSize.argtypes = [SIZE_T, SIZE_T, wintypes.DWORD]
        kernel32.SetSystemFileCacheSize.restype = wintypes.BOOL

        result = kernel32.SetSystemFileCacheSize(SIZE_T(-1), SIZE_T(-1), 0)
        if result:
            kernel32.SetSystemFileCacheSize(SIZE_T(0), SIZE_T(0), 0)
        return bool(result)
    except Exception as e:
        logger.error(f"Error flushing file cache: {e}")
        return False


def smart_clean() -> dict:
    """Perform a comprehensive memory cleaning operation."""
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

    report["processes_trimmed"] = trim_processes_working_sets()
    report["standby_cleared"] = clear_standby_list()
    report["modified_flushed"] = clear_modified_page_list()
    report["cache_flushed"] = flush_system_file_cache()

    after = get_memory_info()
    freed_bytes = after.available - before.available
    report["freed_mb"] = max(0, round(freed_bytes / (1024 ** 2), 1))
    report["after_used_gb"] = after.used_gb
    report["after_percent"] = after.percent
    logger.info(f"Smart clean completed. Freed: {report['freed_mb']} MB")
    return report


def _extract_proc_icon_b64(exe_path):
    """Extract 32x32 PNG Base64 icon from running process executable path."""
    if not exe_path or not isinstance(exe_path, str) or not os.path.exists(exe_path):
        return ""
    if not IS_WIN:
        return ""
    try:
        import win32gui, win32ui, win32con, base64, io
        from PIL import Image

        large, small = win32gui.ExtractIconEx(exe_path, 0)
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


def get_top_memory_processes(count: int = 15) -> list[dict]:
    """Get the top N processes by memory usage with real icons."""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent', 'status', 'exe']):
        try:
            info = proc.info
            if info['memory_info'] is None:
                continue
            mem_mb = info['memory_info'].rss / (1024 ** 2)
            if mem_mb < 1:  # Skip processes using less than 1 MB
                continue

            icon_b64 = _extract_proc_icon_b64(info.get('exe'))

            processes.append({
                'pid': info['pid'],
                'name': info['name'] or 'Unknown',
                'memory_mb': round(mem_mb, 1),
                'memory_percent': round(info['memory_percent'] or 0, 1),
                'status': info['status'],
                'icon_b64': icon_b64,
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

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
    """Check if the current process has administrator / root privileges."""
    try:
        if IS_WIN:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            return os.geteuid() == 0
    except Exception:
        return False


def request_admin_restart() -> None:
    """Restart the application with administrator / root privileges."""
    import sys
    if IS_WIN:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, " ".join(sys.argv), None, 1
        )
    else:
        os.execvp("pkexec", ["pkexec", sys.executable] + sys.argv)
    sys.exit(0)

