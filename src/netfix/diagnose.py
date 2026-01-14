"""Network diagnostic checks."""

from dataclasses import dataclass
from enum import Enum

from .utils import run_cmd, ping, dig, get_default_gateway, get_dns_servers, get_active_interfaces
from .vpn import get_vpn_status


class CheckStatus(Enum):
    OK = "ok"
    WARNING = "warning"
    FAIL = "fail"


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""

    name: str
    status: CheckStatus
    message: str
    details: str | None = None


def check_gateway_reachable() -> DiagnosticResult:
    """Check if default gateway is reachable."""
    gateway = get_default_gateway()
    if not gateway:
        return DiagnosticResult(
            name="Gateway",
            status=CheckStatus.FAIL,
            message="No default gateway found",
        )

    result = ping(gateway, count=1)
    if result.success:
        return DiagnosticResult(
            name="Gateway",
            status=CheckStatus.OK,
            message=f"Gateway {gateway} reachable",
        )
    return DiagnosticResult(
        name="Gateway",
        status=CheckStatus.FAIL,
        message=f"Gateway {gateway} unreachable",
        details=result.stderr,
    )


def check_internet_connectivity() -> DiagnosticResult:
    """Check internet connectivity by pinging 8.8.8.8."""
    result = ping("8.8.8.8", count=3)
    if result.success:
        return DiagnosticResult(
            name="Internet",
            status=CheckStatus.OK,
            message="Internet reachable (8.8.8.8)",
        )
    return DiagnosticResult(
        name="Internet",
        status=CheckStatus.FAIL,
        message="Cannot reach internet (8.8.8.8)",
        details=result.stderr,
    )


def check_dns_resolution() -> DiagnosticResult:
    """Check DNS resolution."""
    test_domains = ["google.com", "cloudflare.com", "apple.com"]
    resolved = []
    failed = []

    for domain in test_domains:
        result = dig(domain)
        if result.success and result.stdout:
            resolved.append(domain)
        else:
            failed.append(domain)

    if len(resolved) == len(test_domains):
        return DiagnosticResult(
            name="DNS Resolution",
            status=CheckStatus.OK,
            message="DNS resolution working",
        )
    elif resolved:
        return DiagnosticResult(
            name="DNS Resolution",
            status=CheckStatus.WARNING,
            message=f"Partial DNS resolution ({len(resolved)}/{len(test_domains)})",
            details=f"Failed: {', '.join(failed)}",
        )
    return DiagnosticResult(
        name="DNS Resolution",
        status=CheckStatus.FAIL,
        message="DNS resolution failing",
        details=f"Cannot resolve: {', '.join(failed)}",
    )


def check_dns_servers() -> DiagnosticResult:
    """Check configured DNS servers."""
    servers = get_dns_servers()
    if not servers:
        return DiagnosticResult(
            name="DNS Servers",
            status=CheckStatus.FAIL,
            message="No DNS servers configured",
        )

    return DiagnosticResult(
        name="DNS Servers",
        status=CheckStatus.OK,
        message=f"{len(servers)} DNS server(s) configured",
        details=", ".join(servers),
    )


def check_network_interfaces() -> DiagnosticResult:
    """Check active network interfaces."""
    interfaces = get_active_interfaces()
    if not interfaces:
        return DiagnosticResult(
            name="Interfaces",
            status=CheckStatus.FAIL,
            message="No active network interfaces",
        )

    iface_info = [f"{i['name']}: {i['ip']}" for i in interfaces]
    return DiagnosticResult(
        name="Interfaces",
        status=CheckStatus.OK,
        message=f"{len(interfaces)} active interface(s)",
        details=", ".join(iface_info),
    )


def check_vpn_status() -> DiagnosticResult:
    """Check VPN connection status."""
    vpn = get_vpn_status()

    if vpn.connected:
        details = []
        if vpn.tunnel_interface:
            details.append(f"tunnel: {vpn.tunnel_interface}")
        if vpn.vpn_dns_servers:
            details.append(f"DNS: {', '.join(vpn.vpn_dns_servers)}")
        details.append(f"{vpn.vpn_routes_count} VPN routes")

        return DiagnosticResult(
            name="VPN",
            status=CheckStatus.OK,
            message="GlobalProtect connected",
            details=" | ".join(details),
        )
    elif vpn.process_running:
        return DiagnosticResult(
            name="VPN",
            status=CheckStatus.WARNING,
            message="GlobalProtect running but not connected",
        )
    return DiagnosticResult(
        name="VPN",
        status=CheckStatus.WARNING,
        message="GlobalProtect not running",
    )


def run_all_diagnostics() -> list[DiagnosticResult]:
    """Run all diagnostic checks."""
    return [
        check_network_interfaces(),
        check_gateway_reachable(),
        check_internet_connectivity(),
        check_dns_servers(),
        check_dns_resolution(),
        check_vpn_status(),
    ]


def get_quick_status() -> dict:
    """Get quick status summary."""
    gateway = get_default_gateway()
    gateway_ok = False
    if gateway:
        result = ping(gateway, count=1)
        gateway_ok = result.success

    internet_result = ping("8.8.8.8", count=1)
    dns_result = dig("google.com")
    vpn = get_vpn_status()
    dns_servers = get_dns_servers()

    return {
        "internet": internet_result.success,
        "gateway": gateway_ok,
        "dns": bool(dns_result.stdout),
        "vpn_connected": vpn.connected,
        "vpn_process": vpn.process_running,
        "dns_servers": dns_servers,
        "vpn_dns": vpn.vpn_dns_servers,
    }
