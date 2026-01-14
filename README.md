# netfix

A CLI tool for diagnosing and repairing network connectivity issues on macOS, with special awareness of GlobalProtect VPN.

## Features

- **Full Diagnostics** - Check gateway, internet, DNS resolution, interfaces, and VPN status
- **Quick Status** - One-line health check for fast troubleshooting
- **VPN Awareness** - Detect GlobalProtect connection state, tunnel interfaces, VPN-assigned DNS, and routing
- **Built-in Fixes** - Flush DNS, renew DHCP, restart Wi-Fi, full network reset
- **Interactive Mode** - Menu-driven fix selection

## Installation

Requires Python 3.12+ and [uv](https://github.com/astral-sh/uv).

```bash
# Clone and install
git clone https://github.com/yourusername/netfix.git
cd netfix
uv sync

# Run with uv
uv run netfix diagnose

# Or install globally
uv tool install .
netfix diagnose
```

## Usage

```bash
# Quick one-line status
netfix status
# Internet: OK | DNS: OK (VPN: 10.0.0.1) | VPN: Connected

# Full diagnostic suite
netfix diagnose

# Interactive fix menu
netfix fix

# Direct fixes
netfix flush-dns      # Flush DNS cache (requires sudo)
netfix reset          # Nuclear option - full network reset

# VPN commands
netfix vpn status     # Connection state and tunnel info
netfix vpn dns        # Compare VPN vs system DNS servers
netfix vpn routes     # Show VPN routing table entries
netfix vpn restart    # Kill and relaunch GlobalProtect
```

## Example Output

```
$ netfix diagnose

Running network diagnostics...

┏━━━━━━━━━━━━━━━━┳━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Check          ┃ Status ┃ Message                 ┃ Details               ┃
┡━━━━━━━━━━━━━━━━╇━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━┩
│ Interfaces     │   OK   │ 3 active interface(s)   │ en0: 192.168.1.100    │
│ Gateway        │   OK   │ Gateway reachable       │                       │
│ Internet       │   OK   │ Internet reachable      │                       │
│ DNS Servers    │   OK   │ 2 DNS server(s)         │ 10.0.0.1, 8.8.8.8     │
│ DNS Resolution │   OK   │ DNS resolution working  │                       │
│ VPN            │   OK   │ GlobalProtect connected │ tunnel: utun0         │
└────────────────┴────────┴─────────────────────────┴───────────────────────┘

All checks passed!
```

## Common Fixes

| Issue | Command |
|-------|---------|
| DNS not resolving | `netfix flush-dns` |
| Stale IP address | `netfix fix` → renew-dhcp |
| Wi-Fi acting weird | `netfix fix` → restart-wifi |
| Everything broken | `netfix reset -y` |

## License

MIT
