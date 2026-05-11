"""
RamBooster - Entry Point
Run this file to start the application.
"""

import ctypes
import logging
import os
import sys


def setup_logging():
    """Configure application logging."""
    log_dir = os.path.join(os.environ.get("APPDATA", "."), "RamBooster")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "rambooster.log")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def set_dpi_awareness():
    """Enable DPI awareness for crisp rendering on high-DPI displays."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Per-monitor DPI aware
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def main():
    """Application entry point."""
    # Setup
    set_dpi_awareness()
    setup_logging()

    logger = logging.getLogger("RamBooster")
    logger.info("=" * 50)
    logger.info("RamBooster starting...")
    logger.info(f"Python: {sys.version}")
    logger.info(f"PID: {os.getpid()}")

    # Check if running as admin
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
        logger.info(f"Admin privileges: {is_admin}")
    except Exception:
        is_admin = False

    # Launch application
    try:
        from ram_booster.app import RamBoosterApp

        app = RamBoosterApp()
        logger.info("Application window created. Starting main loop.")
        app.mainloop()

    except ImportError as e:
        logger.critical(f"Import error: {e}")
        ctypes.windll.user32.MessageBoxW(
            0,
            f"خطأ في تحميل المكتبات:\n{e}\n\nيرجى تثبيت المتطلبات:\npip install -r requirements.txt",
            "RamBooster - خطأ",
            0x10,
        )
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        ctypes.windll.user32.MessageBoxW(
            0,
            f"حدث خطأ غير متوقع:\n{e}",
            "RamBooster - خطأ",
            0x10,
        )
        sys.exit(1)

    logger.info("RamBooster shut down cleanly.")


if __name__ == "__main__":
    main()
