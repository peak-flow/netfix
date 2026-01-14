"""CLI interface for netfix."""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .diagnose import run_all_diagnostics, get_quick_status, CheckStatus
from .fixes import flush_dns, renew_dhcp, restart_wifi, reset_network_services, get_available_fixes
from .vpn import get_vpn_status, get_vpn_routes, restart_globalprotect

app = typer.Typer(
    name="netfix",
    help="Network diagnostic and repair tool for macOS",
    no_args_is_help=True,
)
vpn_app = typer.Typer(help="VPN-related commands")
app.add_typer(vpn_app, name="vpn")

console = Console()


def status_icon(status: CheckStatus) -> str:
    """Get icon for check status."""
    if status == CheckStatus.OK:
        return "[green]OK[/green]"
    elif status == CheckStatus.WARNING:
        return "[yellow]WARN[/yellow]"
    return "[red]FAIL[/red]"


@app.command()
def diagnose():
    """Run full network diagnostics."""
    console.print("\n[bold]Running network diagnostics...[/bold]\n")

    results = run_all_diagnostics()

    table = Table(show_header=True, header_style="bold")
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Message")
    table.add_column("Details", style="dim")

    for result in results:
        table.add_row(
            result.name,
            status_icon(result.status),
            result.message,
            result.details or "",
        )

    console.print(table)

    fails = sum(1 for r in results if r.status == CheckStatus.FAIL)
    warns = sum(1 for r in results if r.status == CheckStatus.WARNING)

    if fails:
        console.print(f"\n[red]Issues found: {fails} failed, {warns} warnings[/red]")
        console.print("Run [cyan]netfix fix[/cyan] to see available fixes\n")
    elif warns:
        console.print(f"\n[yellow]{warns} warning(s)[/yellow]\n")
    else:
        console.print("\n[green]All checks passed![/green]\n")


@app.command()
def status():
    """Quick network status check."""
    s = get_quick_status()

    internet = "[green]OK[/green]" if s["internet"] else "[red]DOWN[/red]"
    dns = "[green]OK[/green]" if s["dns"] else "[red]FAIL[/red]"
    vpn = "[green]Connected[/green]" if s["vpn_connected"] else "[dim]Disconnected[/dim]"

    dns_info = ""
    if s["vpn_dns"]:
        dns_info = f" (VPN: {s['vpn_dns'][0]})"
    elif s["dns_servers"]:
        dns_info = f" ({s['dns_servers'][0]})"

    console.print(f"Internet: {internet} | DNS: {dns}{dns_info} | VPN: {vpn}")


@app.command(name="flush-dns")
def flush_dns_cmd():
    """Flush DNS cache."""
    console.print("[cyan]Flushing DNS cache...[/cyan]")
    result = flush_dns()

    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[red]{result.message}[/red]")


@app.command()
def fix():
    """Interactive fix menu."""
    fixes = get_available_fixes()

    console.print("\n[bold]Available fixes:[/bold]\n")
    for i, fix in enumerate(fixes, 1):
        sudo_note = " [dim](requires sudo)[/dim]" if fix["sudo"] else ""
        console.print(f"  {i}. [cyan]{fix['name']}[/cyan] - {fix['description']}{sudo_note}")

    console.print()
    choice = typer.prompt("Enter fix number (or 'q' to quit)")

    if choice.lower() == 'q':
        return

    try:
        idx = int(choice) - 1
        if 0 <= idx < len(fixes):
            selected = fixes[idx]
            console.print(f"\n[cyan]Running {selected['name']}...[/cyan]")
            result = selected["function"]()
            if result.success:
                console.print(f"[green]{result.message}[/green]\n")
            else:
                console.print(f"[red]{result.message}[/red]\n")
        else:
            console.print("[red]Invalid selection[/red]")
    except ValueError:
        console.print("[red]Invalid input[/red]")


@app.command()
def reset(
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Full network reset (nuclear option)."""
    if not yes:
        confirm = typer.confirm("This will reset DNS, DHCP, and network services. Continue?")
        if not confirm:
            console.print("Aborted.")
            return

    console.print("[cyan]Resetting network services...[/cyan]")
    result = reset_network_services()

    if result.success:
        console.print(f"[green]{result.message}[/green]")
    else:
        console.print(f"[yellow]{result.message}[/yellow]")


@vpn_app.command(name="status")
def vpn_status_cmd():
    """Show VPN connection status."""
    vpn = get_vpn_status()

    if vpn.connected:
        console.print("[green]VPN: Connected[/green]")
        if vpn.tunnel_interface:
            console.print(f"  Tunnel: {vpn.tunnel_interface}")
        if vpn.vpn_dns_servers:
            console.print(f"  DNS: {', '.join(vpn.vpn_dns_servers)}")
        console.print(f"  Routes: {vpn.vpn_routes_count} VPN routes active")
    elif vpn.process_running:
        console.print("[yellow]VPN: Process running but not connected[/yellow]")
    else:
        console.print("[dim]VPN: Not running[/dim]")


@vpn_app.command(name="routes")
def vpn_routes_cmd():
    """Show VPN routing table entries."""
    routes = get_vpn_routes()

    if not routes:
        console.print("[dim]No VPN routes found[/dim]")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Destination")
    table.add_column("Gateway")
    table.add_column("Interface")

    for route in routes[:20]:
        table.add_row(route["destination"], route["gateway"], route["interface"])

    console.print(table)
    if len(routes) > 20:
        console.print(f"[dim]... and {len(routes) - 20} more routes[/dim]")


@vpn_app.command(name="dns")
def vpn_dns_cmd():
    """Show VPN vs system DNS servers."""
    vpn = get_vpn_status()
    from .utils import get_dns_servers

    all_dns = get_dns_servers()

    console.print("\n[bold]DNS Servers:[/bold]")
    for dns in all_dns:
        if dns in vpn.vpn_dns_servers:
            console.print(f"  [cyan]{dns}[/cyan] (VPN)")
        else:
            console.print(f"  {dns}")
    console.print()


@vpn_app.command(name="restart")
def vpn_restart_cmd():
    """Restart GlobalProtect."""
    console.print("[cyan]Restarting GlobalProtect...[/cyan]")
    if restart_globalprotect():
        console.print("[green]GlobalProtect restarted[/green]")
    else:
        console.print("[red]Failed to restart GlobalProtect[/red]")


if __name__ == "__main__":
    app()
