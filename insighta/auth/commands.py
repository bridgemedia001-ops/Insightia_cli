import os
import json
from pathlib import Path
from typing import Optional
import typer
import requests
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from insighta.auth.oauth import OAuthHandler
from insighta.config.credentials import CredentialsManager

console = Console()
credentials_path = Path.home() / ".insighta" / "credentials.json"


def login(
    backend_url: str = typer.Option(
        "http://localhost:8080",
        "--backend-url",
        "-u",
        help="Backend API URL",
    ),
    client_id: str = typer.Option(
        os.getenv("GITHUB_CLIENT_ID", ""),
        "--client-id",
        "-c",
        help="GitHub OAuth client ID",
    ),
):
    credentials_manager = CredentialsManager()

    if credentials_manager.is_logged_in():
        console.print("[yellow]You are already logged in. Use 'insighta logout' first.[/yellow]")
        return

    if not client_id:
        console.print("[red]Error: GitHub client ID is required. Set GITHUB_CLIENT_ID environment variable or use --client-id.[/red]")
        raise typer.Exit(1)

    redirect_uri = "http://localhost:8080/callback"
    oauth = OAuthHandler(client_id, redirect_uri, backend_url)

    console.print("[cyan]Initiating GitHub OAuth login...[/cyan]")
    console.print(f"[dim]Backend URL: {backend_url}[/dim]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Waiting for authentication...", total=None)

        oauth.initiate_login()

        for _ in range(60):
            time.sleep(1)
            if oauth.callback_received:
                progress.update(task, description="Exchanging code for tokens...")
                break

        if not oauth.callback_received:
            console.print("[red]Authentication timed out. Please try again.[/red]")
            raise typer.Exit(1)

    try:
        token_response = oauth.exchange_code_for_tokens()
        credentials_manager.save_credentials(token_response)
        user_info = credentials_manager.get_user_info()
        username = user_info.get("username", "unknown") if user_info else "unknown"
        role = user_info.get("role", "unknown") if user_info else "unknown"
        console.print(f"[green]Successfully logged in as @{username} (role: {role})[/green]")
    except Exception as e:
        console.print(f"[red]Error during authentication: {e}[/red]")
        raise typer.Exit(1)


def logout():
    credentials_manager = CredentialsManager()

    if not credentials_manager.is_logged_in():
        console.print("[yellow]You are not logged in.[/yellow]")
        return

    try:
        credentials = credentials_manager.load_credentials()
        backend_url = os.getenv("INSIGHTA_BACKEND_URL", "http://localhost:8080")

        requests.post(
            f"{backend_url}/auth/logout",
            json={"refresh_token": credentials.get("refresh_token")},
        )
    except Exception:
        pass

    credentials_manager.clear_credentials()
    console.print("[green]Successfully logged out.[/green]")


def whoami():
    credentials_manager = CredentialsManager()

    if not credentials_manager.is_logged_in():
        console.print("[yellow]You are not logged in.[/yellow]")
        return

    credentials = credentials_manager.load_credentials()
    user_info = credentials_manager.get_user_info()
    
    table = Table(title="Current User")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Username", user_info.get("username", "unknown") if user_info else "unknown")
    table.add_row("Role", user_info.get("role", "unknown") if user_info else "unknown")
    table.add_row("Token expires at", credentials.get('expires_at', 'unknown'))
    
    console.print(table)
