"""
web_app.py - PyWebView Bridge for RamBooster Pro System Optimizer.
Connects glassmorphism web UI to all Python backend engines.
"""
import base64
import ctypes
import logging
import os
import sys

import webview

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ram_booster.memory import (
    get_memory_info, get_top_memory_processes, is_admin,
    smart_clean as _smart_clean,
)
from ram_booster.optimizer import get_disk_usage
from ram_booster.disk_cleaner import (
    deep_disk_clean, get_installed_apps as _get_installed_apps,
    uninstall_app as _uninstall_app, analyze_disk_categories as _analyze_disk_categories,
    find_large_files as _find_large_files, get_drive_partitions as _get_drive_partitions,
    delete_specific_file as _delete_specific_file,
)
from ram_booster.game_mode import (
    activate_game_mode, deactivate_game_mode, is_game_mode_active,
    optimize_roblox_and_genshin as _optimize_roblox_and_genshin,
)
from ram_booster.network_optimizer import (
    full_network_optimize, flush_dns, renew_ip, get_network_info,
    get_public_ip_info, set_dns_preset, ping_host, benchmark_dns_servers,
    scan_ports as _scan_ports, get_wifi_info as _get_wifi_info,
    set_static_ip as _set_static_ip, set_dhcp_ip as _set_dhcp_ip,
    set_system_proxy as _set_system_proxy, change_mac_address as _change_mac_address,
    run_speed_test as _run_speed_test, calculate_subnet as _calculate_subnet,
    get_lan_devices as _get_lan_devices, get_active_connections as _get_active_connections,
    get_routing_table as _get_routing_table, get_adapter_diagnostics as _get_adapter_diagnostics,
    discover_path_mtu as _discover_path_mtu, analyze_wifi_spectrum as _analyze_wifi_spectrum,
    inspect_dns_leaks as _inspect_dns_leaks, enable_encrypted_doh as _enable_encrypted_doh,
    trace_gaming_route as _trace_gaming_route, run_jitter_bufferbloat_test as _run_jitter_bufferbloat_test,
    tune_nic_hardware_offloading as _tune_nic_hardware_offloading, apply_qos_gaming_prioritization as _apply_qos_gaming_prioritization,
    get_per_process_bandwidth as _get_per_process_bandwidth, auto_select_fastest_dns as _auto_select_fastest_dns,
    optimize_wifi_tx_power_roaming as _optimize_wifi_tx_power_roaming,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger("RamBooster.WebApp")


class RamBoosterAPI:
    """Full System Optimizer API exposed to JavaScript."""

    # ── RAM ──
    def get_memory(self):
        try:
            m = get_memory_info()
            return {"total": m.total, "available": m.available, "used": m.used,
                    "percent": m.percent, "total_gb": m.total_gb,
                    "available_gb": m.available_gb, "used_gb": m.used_gb}
        except Exception as e:
            return None

    def get_disk(self):
        try: return get_disk_usage("C:\\")
        except: return None

    def get_processes(self):
        try: return get_top_memory_processes(20)
        except: return []

    def smart_clean(self):
        try: return _smart_clean()
        except Exception as e: return {"freed_mb": 0, "error": str(e)}

    # ── Disk & Storage Suite ──
    def deep_clean(self):
        try: return deep_disk_clean()
        except Exception as e: return {"total_freed_mb": 0, "error": str(e)}

    def get_installed_apps(self):
        try: return _get_installed_apps()
        except Exception as e: return []

    def uninstall_app(self, uninstall_cmd):
        try: return _uninstall_app(uninstall_cmd)
        except Exception as e: return {"success": False, "error": str(e)}

    def analyze_disk_categories(self):
        try: return _analyze_disk_categories()
        except Exception as e: return {"audio_mb": 0, "video_mb": 0, "pictures_mb": 0, "documents_mb": 0, "archives_mb": 0}

    def find_large_files(self):
        try: return _find_large_files()
        except Exception as e: return []

    def get_drive_partitions(self):
        try: return _get_drive_partitions()
        except Exception as e: return []

    def delete_specific_file(self, filepath):
        try: return _delete_specific_file(filepath)
        except Exception as e: return {"success": False, "error": str(e)}

    # ── Game Mode ──
    def toggle_game_mode(self):
        try:
            if is_game_mode_active():
                return {"active": False, **deactivate_game_mode()}
            else:
                return {"active": True, **activate_game_mode()}
        except Exception as e:
            return {"error": str(e)}

    def get_game_mode_status(self):
        return is_game_mode_active()

    def boost_roblox_genshin(self):
        try: return _optimize_roblox_and_genshin()
        except Exception as e: return {"success": False, "error": str(e)}

    # ── Network & Telecom/IT Supercharged Tools ──
    def network_optimize(self):
        try: return full_network_optimize()
        except Exception as e: return {"error": str(e)}

    def network_flush_dns(self):
        try: return flush_dns()
        except Exception as e: return {"success": False, "error": str(e)}

    def network_renew_ip(self):
        try: return renew_ip()
        except Exception as e: return {"error": str(e)}

    def network_info(self):
        try: return get_network_info()
        except: return {"interfaces": [], "dns_servers": []}

    def get_public_ip(self):
        try: return get_public_ip_info()
        except Exception as e: return {"ip": "Error", "error": str(e)}

    def set_dns(self, preset):
        try: return set_dns_preset(preset)
        except Exception as e: return {"success": False, "error": str(e)}

    def set_static_ip(self, ip, subnet, gateway):
        try: return _set_static_ip(ip, subnet, gateway)
        except Exception as e: return {"success": False, "error": str(e)}

    def set_dhcp_ip(self):
        try: return _set_dhcp_ip()
        except Exception as e: return {"success": False, "error": str(e)}

    def set_system_proxy(self, enable, proxy_server):
        try: return _set_system_proxy(enable, proxy_server)
        except Exception as e: return {"success": False, "error": str(e)}

    def change_mac_address(self, custom_mac=None):
        try: return _change_mac_address(custom_mac=custom_mac)
        except Exception as e: return {"success": False, "error": str(e)}

    def benchmark_dns(self):
        try: return benchmark_dns_servers()
        except Exception as e: return []

    def ping_target(self, host):
        try: return ping_host(host)
        except Exception as e: return {"host": host, "online": False, "avg_ms": 999, "error": str(e)}

    def scan_ports(self, host):
        try: return _scan_ports(host)
        except Exception as e: return {"target": host, "error": str(e), "open_ports": []}

    def get_wifi_info(self):
        try: return _get_wifi_info()
        except Exception as e: return {"has_wifi": False, "error": str(e)}

    def run_speed_test(self):
        try: return _run_speed_test()
        except Exception as e: return {"success": False, "download_mbps": 0, "upload_mbps": 0, "latency_ms": 0, "error": str(e)}

    def calculate_subnet(self, ip_cidr):
        try: return _calculate_subnet(ip_cidr)
        except Exception as e: return {"success": False, "error": str(e)}

    def get_lan_devices(self):
        try: return _get_lan_devices()
        except Exception as e: return []

    def get_active_connections(self):
        try: return _get_active_connections()
        except Exception as e: return []

    def get_routing_table(self):
        try: return _get_routing_table()
        except Exception as e: return []

    def get_adapter_diagnostics(self):
        try: return _get_adapter_diagnostics()
        except Exception as e: return []

    def discover_path_mtu(self, target="8.8.8.8"):
        try: return _discover_path_mtu(target)
        except Exception as e: return {"optimal_mtu": 1500, "error": str(e)}

    def analyze_wifi_spectrum(self):
        try: return _analyze_wifi_spectrum()
        except Exception as e: return {"success": False, "error": str(e)}

    def inspect_dns_leaks(self):
        try: return _inspect_dns_leaks()
        except Exception as e: return {"success": False, "error": str(e)}

    def enable_encrypted_doh(self):
        try: return _enable_encrypted_doh()
        except Exception as e: return {"success": False, "error": str(e)}

    def trace_gaming_route(self, target="1.1.1.1"):
        try: return _trace_gaming_route(target)
        except Exception as e: return {"success": False, "error": str(e), "hops": []}

    def run_jitter_bufferbloat_test(self, target="1.1.1.1"):
        try: return _run_jitter_bufferbloat_test(target)
        except Exception as e: return {"success": False, "error": str(e)}

    def tune_nic_hardware_offloading(self):
        try: return _tune_nic_hardware_offloading()
        except Exception as e: return {"success": False, "error": str(e)}

    def apply_qos_gaming_prioritization(self):
        try: return _apply_qos_gaming_prioritization()
        except Exception as e: return {"success": False, "error": str(e)}

    def get_per_process_bandwidth(self):
        try: return _get_per_process_bandwidth()
        except Exception as e: return []

    def auto_select_fastest_dns(self):
        try: return _auto_select_fastest_dns()
        except Exception as e: return {"success": False, "error": str(e)}

    def optimize_wifi_tx_power_roaming(self):
        try: return _optimize_wifi_tx_power_roaming()
        except Exception as e: return {"success": False, "error": str(e)}

    # ── System Controls ──
    def kill_process(self, pid):
        """Terminate a process by PID."""
        try:
            import psutil
            pid = int(pid)
            p = psutil.Process(pid)
            name = p.name()
            p.kill()
            return {"success": True, "pid": pid, "name": name}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def system_boost(self):
        """Run system boost (temp clean + standby list trim)."""
        try:
            from ram_booster.optimizer import system_boost as _system_boost
            return _system_boost()
        except Exception as e:
            return {"error": str(e)}

    def get_sys_info(self):
        """Get host system hardware details."""
        try:
            import platform, psutil
            cpu_name = platform.processor() or "x86/x64 Processor"
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
                cpu_name, _ = winreg.QueryValueEx(k, "ProcessorNameString")
                winreg.CloseKey(k)
            except: pass

            mem = psutil.virtual_memory()
            return {
                "os": f"Windows {platform.release()} ({platform.version()})",
                "cpu": cpu_name.strip(),
                "cores": psutil.cpu_count(logical=True),
                "ram_total_gb": round(mem.total / (1024**3), 1),
                "is_admin": is_admin(),
            }
        except Exception as e:
            return {"os": "Windows", "cpu": "Unknown", "cores": 0, "ram_total_gb": 0, "is_admin": False}

    def get_deep_system_diagnostics(self):
        """Fetch ultra deep hardware, BIOS, GPU, RAM, NVMe & Motherboard metrics."""
        try:
            from ram_booster.sys_inspector import get_deep_system_diagnostics as _get_deep_sys
            return _get_deep_sys()
        except Exception as e:
            return {"error": str(e)}

    def open_url(self, url):
        """Open external URL in default web browser."""
        try:
            import webbrowser
            webbrowser.open(url)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def is_admin(self):
        return is_admin()

    def get_icon_path(self):
        try:
            base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
            for p in [os.path.join(base, "ram_booster", "icon_web.png"), os.path.join(base, "web", "icon_web.png"), os.path.join(base, "icon_web.png")]:
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
            return None
        except: return None


def main():
    try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except: pass

    logger.info("RamBooster Pro System Optimizer starting...")
    base = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
    html = os.path.join(base, "web", "index.html")

    ico = os.path.join(base, "icon.ico")
    if not os.path.exists(ico): ico = None

    window = webview.create_window(
        title="RAM Booster Pro — System Optimizer",
        url=html, js_api=RamBoosterAPI(),
        width=1200, height=760, min_size=(1000, 650),
        background_color="#050510",
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
