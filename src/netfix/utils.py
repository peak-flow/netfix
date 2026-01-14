"""Utility functions for running system commands."""

import subprocess
from dataclasses import dataclass


@dataclass
class CommandResult:
    """Result of a shell command execution."""

    stdout: str
    stderr: str
    returncode: int

    @property
    def success(self) -> bool:
        return self.returncode == 0


def run_cmd(cmd: str | list[str], timeout: int = 30, sudo: bool = False) -> CommandResult:
    """Run a shell command and return the result."""
    if isinstance(cmd, str):
        shell = True
        if sudo:
            cmd = f"sudo {cmd}"
    else:
        shell = False
        if sudo:
            cmd = ["sudo"] + cmd

    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return CommandResult(
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        return CommandResult(stdout="", stderr="Command timed out", returncode=-1)
    except Exception as e:
        return CommandResult(stdout="", stderr=str(e), returncode=-1)


def ping(host: str, count: int = 1, timeout: int = 5) -> CommandResult:
    """Ping a host."""
    return run_cmd(f"ping -c {count} -t {timeout} {host}", timeout=timeout + 5)


def dig(domain: str, record_type: str = "A") -> CommandResult:
    """DNS lookup using dig."""
    return run_cmd(f"dig +short {record_type} {domain}", timeout=10)


def get_default_gateway() -> str | None:
    """Get the default gateway IP address."""
    result = run_cmd("netstat -rn | grep 'default' | head -1 | awk '{print $2}'")
    if result.success and result.stdout:
        return result.stdout.split()[0] if result.stdout else None
    return None


def get_dns_servers() -> list[str]:
    """Get configured DNS servers."""
    result = run_cmd("scutil --dns | grep 'nameserver' | awk '{print $3}'")
    if result.success:
        return list(set(result.stdout.split()))
    return []


def get_active_interfaces() -> list[dict]:
    """Get active network interfaces with IP addresses."""
    result = run_cmd("ifconfig | grep -E '^[a-z]|inet '")
    if not result.success:
        return []

    interfaces = []
    current_iface = None

    for line in result.stdout.split("\n"):
        if line and not line.startswith("\t") and not line.startswith(" "):
            current_iface = line.split(":")[0]
        elif "inet " in line and current_iface:
            parts = line.strip().split()
            if len(parts) >= 2:
                ip = parts[1]
                if not ip.startswith("127."):
                    interfaces.append({"name": current_iface, "ip": ip})

    return interfaces
