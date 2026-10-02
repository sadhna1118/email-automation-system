import sys
import os
import argparse
import uvicorn
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

from config import Config
from database import EmailDatabase
from email_sender import EmailSender
from email_monitor import EmailMonitor
from template_engine import TemplateEngine
from validator import EmailValidator
from campaign_engine import CampaignEngine
from scheduler import EmailScheduler
import seed_demo_data

console = Console()

def print_banner():
    """Display rich terminal banner"""
    banner = """
   ___                 __  ___      _ __  ____           
  / _ |__ ________ _  /  |/  /___ _(_) / / __ \___ ___  
 / __ / // / __/ _ `/ / /|_/ / _ `/ / / / /_/ / _ (_-<  
/_/ |_\_,_/_/  \_,_/ /_/  /_/\_,_/_/_/  \____/ .__/___/  
                                            /_/          
         Enterprise Email Automation & Intelligence OS   
    """
    console.print(Panel(banner, style="bold cyan", subtitle="[bold white]v2.0.0 Pro[/bold white]"))

def print_menu():
    """Display colorized interactive CLI menu"""
    table = Table(title="[bold magenta]Control Center Menu[/bold magenta]", show_header=True, header_style="bold blue")
    table.add_column("#", style="dim", width=4)
    table.add_column("Action", style="bold white")
    table.add_column("Description", style="dim")

    table.add_row("1", "🚀 Launch Web Dashboard", "Start the modern glassmorphism Web UI & REST API")
    table.add_row("2", "✉️  Send Single Email", "Compose and send one-off email with live tracking")
    table.add_row("3", "📁 Send Bulk CSV Emails", "Broadcast personalized templates with batch throttling")
    table.add_row("4", "📥 Start Inbox Monitor", "Listen for incoming IMAP messages & trigger smart rules")
    table.add_row("5", "⚡ Manage Smart Rules", "Configure trigger rules (alerts, auto-replies, webhooks)")
    table.add_row("6", "📊 View Analytics Digest", "View delivery rates, open/click counts, and trends")
    table.add_row("7", "⏱️  Run Background Scheduler", "Execute persistent recurring tasks & digests")
    table.add_row("8", "🌱 Seed Demo Dataset", "Populate database with sample contacts, templates, and rules")
    table.add_row("9", "🚪 Exit", "Close the application")

    console.print(table)

def run_streamlit(host=None, port=None):
    """Start the Streamlit Web Application"""
    host = host or "0.0.0.0"
    port = port or 8501
    console.print(f"\n[bold green]🚀 Launching Email Automation Streamlit Dashboard at http://localhost:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop dashboard[/dim]\n")
    import subprocess
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", str(port), "--server.address", host])

def run_web_server(host=None, port=None):
    """Start the FastAPI Web Server and Dashboard"""
    host = host or Config.WEB_HOST
    port = port or Config.WEB_PORT
    console.print(f"\n[bold green]🚀 Launching AuraMail API Server at http://{host}:{port}[/bold green]")
    console.print("[dim]Press Ctrl+C to stop web server[/dim]\n")
    uvicorn.run("api:app", host=host, port=port, reload=False)

def cli_send_single():
    """CLI wizard to send single email"""
    sender = EmailSender()
    to_email = Prompt.ask("[cyan]Recipient Email[/cyan]")
    subject = Prompt.ask("[cyan]Subject Line[/cyan]")
    body = Prompt.ask("[cyan]Body Content[/cyan]")
    is_html = Confirm.ask("[cyan]Send as Rich HTML?[/cyan]", default=True)

    console.print("\n[yellow]Transmitting message...[/yellow]")
    ok = sender.send_email(to_email=to_email, subject=subject, body=body, html=is_html)
    if ok:
        console.print(f"[bold green]✓ Message successfully sent to {to_email}[/bold green]")
    else:
        console.print(f"[bold red]✕ Failed to send message to {to_email}. Check logs.[/bold red]")

def cli_send_bulk():
    """CLI wizard for bulk sending"""
    sender = EmailSender()
    csv_file = Prompt.ask("[cyan]CSV File Path[/cyan]", default="sample_recipients.csv")
    
    if not os.path.exists(csv_file):
        console.print(f"[bold red]File not found: {csv_file}[/bold red]")
        return
    
    subject_template = Prompt.ask("[cyan]Subject Template (use {name}, {company})[/cyan]", default="Hello {name}, updates from {company}!")
    body_template = Prompt.ask("[cyan]Body Template[/cyan]", default="Hi {name},\n\nWe have excited updates for you at {company}.\n\nBest regards,\nTeam")
    is_html = Confirm.ask("[cyan]Send as Rich HTML?[/cyan]", default=False)

    console.print("\n[yellow]Starting bulk dispatch...[/yellow]")
    success, failed = sender.send_bulk_emails(csv_file, subject_template, body_template, html=is_html)
    console.print(f"\n[bold green]✓ Bulk Transmission Complete! Sent: {success} | Failed: {failed}[/bold green]")

def cli_view_stats():
    """Display full platform analytics in terminal"""
    db = EmailDatabase()
    stats = db.get_email_stats()

    grid = Table.grid(expand=True)
    grid.add_column()
    grid.add_column()

    stats_table = Table(title="[bold green]Platform Performance Analytics[/bold green]", show_header=True, header_style="bold cyan")
    stats_table.add_column("Metric", style="bold")
    stats_table.add_column("Value", style="bold white")

    stats_table.add_row("Total Sent Emails", str(stats['sent']))
    stats_table.add_row("Delivery Success Rate", f"{stats['delivery_rate']}%")
    stats_table.add_row("Failed Transmissions", str(stats['failed']))
    stats_table.add_row("Email Opens Recorded", f"{stats['opened']} ({stats['open_rate']}%)")
    stats_table.add_row("Click Tracking Conversions", f"{stats['clicked']} ({stats['click_rate']}%)")
    stats_table.add_row("Monitored Incoming Messages", str(stats['monitored']))
    stats_table.add_row("Active Subscribers in DB", str(stats['active_contacts']))
    stats_table.add_row("Configured Smart Rules", str(stats['active_rules']))
    stats_table.add_row("Simulation Mode Active", str(Config.DRY_RUN))

    console.print(stats_table)

def cli_monitor_inbox():
    """Start continuous inbox monitor in foreground"""
    monitor = EmailMonitor()
    interval = int(Prompt.ask("[cyan]Check interval in seconds[/cyan]", default=str(Config.CHECK_INTERVAL)))
    monitor.start_monitoring(interval=interval)

def main():
    """Main CLI entrypoint with argument parsing and interactive fallback"""
    parser = argparse.ArgumentParser(description="AuraMail Pro — Enterprise Email Automation & Intelligence OS")
    parser.add_argument("-w", "--web", action="store_true", help="Launch the Streamlit Web Dashboard")
    parser.add_argument("--streamlit", action="store_true", help="Launch the Streamlit Web Dashboard")
    parser.add_argument("--api", action="store_true", help="Launch the FastAPI REST API Server")
    parser.add_argument("--port", type=int, default=8501, help="Port for web dashboard (default 8501)")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host for web server (default 0.0.0.0)")
    parser.add_argument("-s", "--stats", action="store_true", help="Display platform analytics in terminal")
    parser.add_argument("--seed", action="store_true", help="Seed database with enterprise demo dataset")
    parser.add_argument("-m", "--monitor", action="store_true", help="Start continuous IMAP email monitoring")
    parser.add_argument("-b", "--bulk", type=str, help="Send bulk emails with path to CSV file")
    parser.add_argument("--dry-run", action="store_true", help="Force dry-run simulation mode")

    args = parser.parse_args()

    if args.dry_run:
        Config.DRY_RUN = True

    if args.seed:
        seed_demo_data.seed()
        return

    if args.stats:
        print_banner()
        cli_view_stats()
        return

    if args.monitor:
        print_banner()
        monitor = EmailMonitor()
        monitor.start_monitoring()
        return

    if args.bulk:
        print_banner()
        sender = EmailSender()
        sender.send_bulk_emails(args.bulk, "Update for {name}", "Hello {name}, welcome to {company}!")
        return

    if args.api:
        print_banner()
        run_web_server(host=args.host, port=Config.WEB_PORT)
        return

    if args.web or args.streamlit:
        print_banner()
        run_streamlit(host=args.host, port=args.port)
        return

    # If no flags passed, launch interactive menu
    print_banner()
    while True:
        try:
            print_menu()
            choice = Prompt.ask("\n[bold cyan]Select an option (1-9)[/bold cyan]", choices=["1","2","3","4","5","6","7","8","9"], default="1")

            if choice == "1":
                run_streamlit(port=args.port)
                break
            elif choice == "2":
                cli_send_single()
            elif choice == "3":
                cli_send_bulk()
            elif choice == "4":
                cli_monitor_inbox()
            elif choice == "5":
                db = EmailDatabase()
                rules = db.get_all_rules()
                t = Table(title="Configured Smart Rules")
                t.add_column("Rule Name")
                t.add_column("Action")
                t.add_column("Status")
                for r in rules:
                    t.add_row(r['rule_name'], r['action_type'], "Active" if r['enabled'] else "Disabled")
                console.print(t)
            elif choice == "6":
                cli_view_stats()
            elif choice == "7":
                scheduler = EmailScheduler()
                scheduler.run()
            elif choice == "8":
                seed_demo_data.seed()
            elif choice == "9":
                console.print("[bold yellow]Exiting AuraMail Pro. Goodbye![/bold yellow]")
                sys.exit(0)
        except KeyboardInterrupt:
            console.print("\n[bold yellow]Session ended.[/bold yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")

if __name__ == '__main__':
    main()