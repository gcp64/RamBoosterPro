"""
power_monitor.py - Power & Battery Monitor Engine.
Detects hardware type (Laptop/Desktop), reads battery stats,
and provides smart charge alerts via Windows Toast Notifications.
"""
import logging
import threading
import time
import subprocess
import psutil

logger = logging.getLogger("RamBooster.PowerMonitor")

# Smart alert state
_alert_enabled = False
_alert_threshold_high = 80  # Stop charging alert
_alert_threshold_low = 20   # Plug in alert
_alert_thread = None
_alert_running = False


def detect_hardware():
    """Detect if system is Laptop or Desktop."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {
                "type": "desktop",
                "has_battery": False,
                "message": "Desktop System Detected - Direct Power Mode",
                "message_ar": "نظام مكتبي - وضع الطاقة المباشرة",
            }
        else:
            return {
                "type": "laptop",
                "has_battery": True,
                "message": "Laptop System Detected - Battery Mode",
                "message_ar": "نظام محمول - وضع البطارية",
            }
    except Exception as e:
        logger.error(f"Hardware detection error: {e}")
        return {
            "type": "unknown",
            "has_battery": False,
            "message": "Could not detect hardware type",
            "message_ar": "تعذر اكتشاف نوع الجهاز",
        }


def get_battery_status():
    """Get current battery percentage and charging state."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return {
                "has_battery": False,
                "percent": -1,
                "plugged": False,
                "time_left": "N/A",
                "status": "desktop",
                "status_ar": "مكتبي",
            }

        # Calculate time remaining
        secs = battery.secsleft
        if secs == psutil.POWER_TIME_UNLIMITED:
            time_str = "Charging..."
            time_ar = "جاري الشحن..."
        elif secs == psutil.POWER_TIME_UNKNOWN or secs < 0:
            time_str = "Calculating..."
            time_ar = "جاري الحساب..."
        else:
            hours = secs // 3600
            mins = (secs % 3600) // 60
            time_str = f"{hours}h {mins}m remaining"
            time_ar = f"{hours} ساعة {mins} دقيقة متبقية"

        # Determine status
        pct = round(battery.percent)
        if battery.power_plugged:
            if pct >= 100:
                status = "Fully Charged"
                status_ar = "مشحون بالكامل"
            else:
                status = "Charging"
                status_ar = "جاري الشحن"
        else:
            if pct <= 10:
                status = "Critical"
                status_ar = "حرج"
            elif pct <= 20:
                status = "Low Battery"
                status_ar = "بطارية منخفضة"
            elif pct <= 50:
                status = "Moderate"
                status_ar = "متوسط"
            else:
                status = "Good"
                status_ar = "جيد"

        return {
            "has_battery": True,
            "percent": pct,
            "plugged": battery.power_plugged,
            "time_left": time_str,
            "time_left_ar": time_ar,
            "status": status,
            "status_ar": status_ar,
        }
    except Exception as e:
        logger.error(f"Battery status error: {e}")
        return {
            "has_battery": False,
            "percent": -1,
            "plugged": False,
            "time_left": "Error",
            "status": "error",
        }


def get_power_plan():
    """Get current Windows power plan."""
    try:
        r = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        if r.returncode == 0:
            out = r.stdout.strip()
            # Extract plan name from output like:
            # "Power Scheme GUID: xxx  (Balanced)"
            if "(" in out and ")" in out:
                name = out.split("(")[-1].rstrip(")")
                return {"plan": name, "raw": out}
        return {"plan": "Unknown", "raw": ""}
    except Exception:
        return {"plan": "Unknown", "raw": ""}


def set_power_plan(plan_type):
    """Set Windows power plan. plan_type: 'high', 'balanced', 'saver'."""
    plans = {
        "high": "8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c",
        "balanced": "381b4222-f694-41f0-9685-ff5bb260df2e",
        "saver": "a1841308-3541-4fab-bc81-f71556f20b4a",
    }
    guid = plans.get(plan_type)
    if not guid:
        return {"success": False, "error": "Invalid plan type"}
    try:
        subprocess.run(
            ["powercfg", "/setactive", guid],
            capture_output=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return {"success": True, "plan": plan_type}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _send_windows_notification(title, message):
    """Send Windows Toast Notification via PowerShell."""
    try:
        ps_script = f"""
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $textNodes = $template.GetElementsByTagName("text")
        $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}")) > $null
        $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}")) > $null
        $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
        [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("RamBooster Pro").Show($toast)
        """
        subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        return True
    except Exception as e:
        logger.error(f"Notification error: {e}")
        return False


def _alert_loop():
    """Background thread for smart charge alerts."""
    global _alert_running
    _alert_running = True
    notified_high = False
    notified_low = False

    while _alert_running and _alert_enabled:
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                time.sleep(30)
                continue

            pct = round(battery.percent)

            # High threshold alert (stop charging)
            if pct >= _alert_threshold_high and battery.power_plugged and not notified_high:
                _send_windows_notification(
                    "RamBooster Pro - Smart Charge",
                    f"Battery at {pct}%! Unplug charger to preserve battery health."
                )
                notified_high = True
                notified_low = False
                logger.info(f"High charge alert sent: {pct}%")

            # Low threshold alert (plug in)
            elif pct <= _alert_threshold_low and not battery.power_plugged and not notified_low:
                _send_windows_notification(
                    "RamBooster Pro - Low Battery",
                    f"Battery at {pct}%! Plug in charger now."
                )
                notified_low = True
                notified_high = False
                logger.info(f"Low charge alert sent: {pct}%")

            # Reset when back to normal range
            if _alert_threshold_low < pct < _alert_threshold_high:
                notified_high = False
                notified_low = False

            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            logger.error(f"Alert loop error: {e}")
            time.sleep(30)

    _alert_running = False


def enable_smart_alert(high=80, low=20):
    """Enable smart charge alert with thresholds."""
    global _alert_enabled, _alert_threshold_high, _alert_threshold_low, _alert_thread
    _alert_threshold_high = high
    _alert_threshold_low = low
    _alert_enabled = True

    if _alert_thread is None or not _alert_thread.is_alive():
        _alert_thread = threading.Thread(target=_alert_loop, daemon=True)
        _alert_thread.start()

    logger.info(f"Smart alert ON: high={high}%, low={low}%")
    return {
        "enabled": True,
        "high": high,
        "low": low,
    }


def disable_smart_alert():
    """Disable smart charge alert."""
    global _alert_enabled, _alert_running
    _alert_enabled = False
    _alert_running = False
    logger.info("Smart alert OFF")
    return {"enabled": False}


def is_alert_enabled():
    """Check if smart alert is active."""
    return {
        "enabled": _alert_enabled,
        "high": _alert_threshold_high,
        "low": _alert_threshold_low,
    }
