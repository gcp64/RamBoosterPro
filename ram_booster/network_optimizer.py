"""
network_optimizer.py - Network & Ping Optimizer Engine.
Flush DNS, renew IP, optimize TCP/IP settings for gaming.
"""
import logging
import subprocess

logger = logging.getLogger("RamBooster.NetworkOptimizer")

SW = subprocess.CREATE_NO_WINDOW


def _run_cmd(cmd, timeout=15):
    """Run a command and return (success, output)."""
    try:
        r = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=timeout, creationflags=SW,
        )
        return r.returncode == 0, r.stdout.strip()
    except Exception as e:
        return False, str(e)


def flush_dns():
    """Flush DNS resolver cache."""
    ok, out = _run_cmd(["ipconfig", "/flushdns"])
    logger.info(f"DNS flush: {'OK' if ok else 'FAIL'}")
    return {"success": ok, "output": out}


def renew_ip():
    """Release and renew IP address."""
    results = {}
    ok1, _ = _run_cmd(["ipconfig", "/release"], timeout=20)
    results["release"] = ok1
    ok2, _ = _run_cmd(["ipconfig", "/renew"], timeout=30)
    results["renew"] = ok2
    logger.info(f"IP renew: release={ok1}, renew={ok2}")
    return results


def reset_winsock():
    """Reset Winsock catalog to clean state."""
    ok, out = _run_cmd(["netsh", "winsock", "reset"])
    logger.info(f"Winsock reset: {'OK' if ok else 'FAIL'}")
    return {"success": ok, "output": out}


def optimize_tcp():
    """Optimize TCP/IP settings for low latency gaming."""
    results = {"applied": 0, "failed": 0, "details": []}

    commands = [
        # Enable TCP auto-tuning (normal = auto-adjusting window)
        (["netsh", "int", "tcp", "set", "global", "autotuninglevel=normal"],
         "TCP Auto-Tuning: Normal"),
        # Disable TCP timestamps (reduces overhead)
        (["netsh", "int", "tcp", "set", "global", "timestamps=disabled"],
         "TCP Timestamps: Disabled"),
        # Enable Direct Cache Access
        (["netsh", "int", "tcp", "set", "global", "dca=enabled"],
         "Direct Cache Access: Enabled"),
        # Disable TCP chimney offload (better for gaming)
        (["netsh", "int", "tcp", "set", "global", "chimney=disabled"],
         "TCP Chimney: Disabled"),
        # Enable ECN capability
        (["netsh", "int", "tcp", "set", "global", "ecncapability=enabled"],
         "ECN Capability: Enabled"),
        # Set congestion provider to CTCP (Compound TCP - better for gaming)
        (["netsh", "int", "tcp", "set", "supplemental", "template=Internet",
          "congestionprovider=ctcp"],
         "Congestion Provider: CTCP"),
        # Disable Nagle's algorithm delay via registry
        (["reg", "add",
          r"HKLM\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters",
          "/v", "TcpNoDelay", "/t", "REG_DWORD", "/d", "1", "/f"],
         "Nagle's Algorithm: Disabled"),
        # Disable network throttling
        (["reg", "add",
          r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
          "/v", "NetworkThrottlingIndex", "/t", "REG_DWORD",
          "/d", "4294967295", "/f"],
         "Network Throttling: Disabled"),
        # Set system responsiveness to 0 (dedicate all resources)
        (["reg", "add",
          r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile",
          "/v", "SystemResponsiveness", "/t", "REG_DWORD", "/d", "0", "/f"],
         "System Responsiveness: Maximum"),
    ]

    for cmd, desc in commands:
        ok, _ = _run_cmd(cmd)
        if ok:
            results["applied"] += 1
            results["details"].append(f"✓ {desc}")
        else:
            results["failed"] += 1
            results["details"].append(f"✗ {desc}")

    logger.info(f"TCP optimized: {results['applied']}/{len(commands)}")
    return results


def clear_arp_cache():
    """Clear ARP cache."""
    ok, _ = _run_cmd(["netsh", "interface", "ip", "delete", "arpcache"])
    return {"success": ok}


def get_network_info():
    """Get current network stats."""
    try:
        ok, out = _run_cmd(["netsh", "interface", "show", "interface"])
        interfaces = []
        if ok:
            for line in out.split("\n")[3:]:
                parts = line.split()
                if len(parts) >= 4:
                    interfaces.append({
                        "state": parts[0],
                        "type": parts[1],
                        "name": " ".join(parts[3:]),
                    })
        # Get DNS servers
        ok2, dns_out = _run_cmd(
            ["powershell", "-Command",
             "Get-DnsClientServerAddress -AddressFamily IPv4 | "
             "Select-Object -ExpandProperty ServerAddresses | "
             "Select-Object -First 4"]
        )
        dns_servers = dns_out.strip().split("\n") if ok2 else []

        return {
            "interfaces": interfaces,
            "dns_servers": [d.strip() for d in dns_servers if d.strip()],
        }
    except Exception as e:
        logger.error(f"Network info error: {e}")
        return {"interfaces": [], "dns_servers": []}


def full_network_optimize():
    """Run all network optimizations."""
    results = {
        "dns_flush": False,
        "tcp_applied": 0,
        "arp_cleared": False,
        "details": [],
    }

    # 1. Flush DNS
    dns = flush_dns()
    results["dns_flush"] = dns["success"]
    results["details"].append("DNS Cache Flushed" if dns["success"] else "DNS Flush Failed")

    # 2. Clear ARP
    arp = clear_arp_cache()
    results["arp_cleared"] = arp["success"]
    results["details"].append("ARP Cache Cleared" if arp["success"] else "ARP Clear Failed")

    # 3. Optimize TCP
    tcp = optimize_tcp()
    results["tcp_applied"] = tcp["applied"]
    results["details"].extend(tcp["details"])

    logger.info(f"Full network optimize done: DNS={results['dns_flush']}, TCP={results['tcp_applied']}")
    return results
