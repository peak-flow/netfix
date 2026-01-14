"""Network fix and repair commands."""

from dataclasses import dataclass

from .utils import run_cmd


@dataclass
class FixResult:
    """Result of a fix operation."""

    name: str
    success: bool
    message: str
    requires_sudo: bool = False


def flush_dns() -> FixResult:
    """Flush DNS cache."""
    result1 = run_cmd("dscacheutil -flushcache", sudo=True)
    result2 = run_cmd("killall -HUP mDNSResponder", sudo=True)

    success = result1.success or result2.success
    return FixResult(
        name="Flush DNS",
        success=success,
        message="DNS cache flushed" if success else "Failed to flush DNS cache",
        requires_sudo=True,
    )


def renew_dhcp(interface: str = "en0") -> FixResult:
    """Renew DHCP lease on interface."""
    result = run_cmd(["ipconfig", "set", interface, "DHCP"])
    return FixResult(
        name="Renew DHCP",
        success=result.success,
        message=f"DHCP renewed on {interface}" if result.success else f"Failed to renew DHCP: {result.stderr}",
    )


def restart_wifi() -> FixResult:
    """Turn Wi-Fi off and on again."""
    off_result = run_cmd("networksetup -setairportpower en0 off")
    if not off_result.success:
        return FixResult(
            name="Restart Wi-Fi",
            success=False,
            message="Failed to turn off Wi-Fi",
        )

    import time
    time.sleep(2)

    on_result = run_cmd("networksetup -setairportpower en0 on")
    return FixResult(
        name="Restart Wi-Fi",
        success=on_result.success,
        message="Wi-Fi restarted" if on_result.success else "Failed to turn on Wi-Fi",
    )


def reset_network_services() -> FixResult:
    """Reset all network services (nuclear option)."""
    results = []

    flush_result = flush_dns()
    results.append(flush_result.success)

    renew_result = renew_dhcp()
    results.append(renew_result.success)

    mdns_result = run_cmd("killall -9 mDNSResponder", sudo=True)
    results.append(mdns_result.success)

    success = sum(results) >= 2
    return FixResult(
        name="Reset Network",
        success=success,
        message="Network services reset" if success else "Some reset operations failed",
        requires_sudo=True,
    )


def get_available_fixes() -> list[dict]:
    """Get list of available fixes with descriptions."""
    return [
        {
            "name": "flush-dns",
            "description": "Flush DNS cache (clears cached DNS lookups)",
            "function": flush_dns,
            "sudo": True,
        },
        {
            "name": "renew-dhcp",
            "description": "Renew DHCP lease (get fresh IP configuration)",
            "function": renew_dhcp,
            "sudo": False,
        },
        {
            "name": "restart-wifi",
            "description": "Turn Wi-Fi off and on",
            "function": restart_wifi,
            "sudo": False,
        },
        {
            "name": "reset-network",
            "description": "Full network stack reset (DNS + DHCP + mDNSResponder)",
            "function": reset_network_services,
            "sudo": True,
        },
    ]
