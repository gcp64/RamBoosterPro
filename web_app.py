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
from ram_booster.disk_cleaner import deep_disk_clean
from ram_booster.game_mode import (
    activate_game_mode, deactivate_game_mode, is_game_mode_active,
)
from ram_booster.network_optimizer import (
    full_network_optimize, flush_dns, renew_ip, get_network_info,
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

    # ── Disk ──
    def deep_clean(self):
        try: return deep_disk_clean()
        except Exception as e: return {"total_freed_mb": 0, "error": str(e)}

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

    # ── Network ──
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

    # ── System ──
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
