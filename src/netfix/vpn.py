"""VPN detection and management for GlobalProtect."""

from dataclasses import dataclass

from .utils import run_cmd


@dataclass
class VPNStatus:
    """VPN connection status."""

    connected: bool
    process_running: bool
    tunnel_interface: str | None
    vpn_dns_servers: list[str]
    vpn_routes_count: int


def is_globalprotect_running() -> bool:
    """Check if GlobalProtect process is running."""
    result = run_cmd("pgrep -i globalprotect")
    return result.success and bool(result.stdout)


def get_vpn_tunnel_interface() -> str | None:
    """Get the VPN tunnel interface (utun) if active."""
    result = run_cmd("ifconfig | grep -E '^utun.*UP' | head -1 | cut -d: -f1")
    if result.success and result.stdout:
        return result.stdout.split()[0]
    return None


def get_vpn_routes() -> list[dict]:
    """Get routes going through VPN tunnel interfaces."""
    result = run_cmd("netstat -rn | grep utun")
    if not result.success:
        return []

    routes = []
    for line in result.stdout.split("\n"):
        if line.strip():
            parts = line.split()
            if len(parts) >= 4:
                routes.append({
                    "destination": parts[0],
                    "gateway": parts[1],
                    "interface": parts[3] if len(parts) > 3 else parts[-1],
                })
    return routes


def get_vpn_dns_servers() -> list[str]:
    """Get DNS servers assigned by VPN (typically 10.x.x.x ranges)."""
    result = run_cmd("scutil --dns | grep -A 5 'resolver #' | grep nameserver | awk '{print $3}'")
    if not result.success:
        return []

    vpn_dns = []
    for dns in result.stdout.split():
        if dns.startswith("10.") or dns.startswith("172.") or dns.startswith("192.168."):
            vpn_dns.append(dns)
    return list(set(vpn_dns))


def get_vpn_status() -> VPNStatus:
    """Get comprehensive VPN status."""
    process_running = is_globalprotect_running()
    tunnel_iface = get_vpn_tunnel_interface()
    vpn_routes = get_vpn_routes()
    vpn_dns = get_vpn_dns_servers()

    connected = bool(tunnel_iface) or len(vpn_routes) > 0

    return VPNStatus(
        connected=connected,
        process_running=process_running,
        tunnel_interface=tunnel_iface,
        vpn_dns_servers=vpn_dns,
        vpn_routes_count=len(vpn_routes),
    )


def restart_globalprotect() -> bool:
    """Restart GlobalProtect by killing and relaunching."""
    kill_result = run_cmd("pkill -9 -i globalprotect")

    import time
    time.sleep(2)

    launch_result = run_cmd("open -a 'GlobalProtect'")
    return launch_result.success
