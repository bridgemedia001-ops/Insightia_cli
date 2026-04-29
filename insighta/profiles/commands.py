import os
import csv
import time
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from insighta.api.client import APIClient

console = Console()


def list_profiles(
    gender: Optional[str] = typer.Option(None, "--gender", "-g", help="Filter by gender"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Filter by country ID"),
    age_group: Optional[str] = typer.Option(None, "--age-group", help="Filter by age group"),
    min_age: Optional[int] = typer.Option(None, "--min-age", help="Minimum age"),
    max_age: Optional[int] = typer.Option(None, "--max-age", help="Maximum age"),
    sort_by: str = typer.Option("created_at", "--sort-by", "-s", help="Sort field"),
    order: str = typer.Option("asc", "--order", "-o", help="Sort order (asc/desc)"),
    page: int = typer.Option(1, "--page", "-p", help="Page number"),
    limit: int = typer.Option(10, "--limit", "-l", help="Items per page"),
):
    client = APIClient()

    params = {
        "page": page,
        "limit": limit,
        "sortBy": sort_by,
        "order": order,
    }

    if gender:
        params["gender"] = gender
    if country:
        params["country_id"] = country
    if age_group:
        params["age_group"] = age_group
    if min_age:
        params["min_age"] = min_age
    if max_age:
        params["max_age"] = max_age

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching profiles...", total=None)
        response = client.get("/api/profiles", params=params)

    if response.status_code != 200:
        console.print(f"[red]Error fetching profiles: {response.status_code}[/red]")
        console.print(response.text)
        raise typer.Exit(1)

    data = response.json()

    table = Table(title=f"Profiles (Page {data.get('page', 1)} of {data.get('total_pages', 1)})")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Gender", style="green")
    table.add_column("Age", style="yellow")
    table.add_column("Country", style="blue")

    for profile in data.get("data", []):
        table.add_row(
            str(profile.get("id", ""))[:8] + "...",
            profile.get("name", ""),
            profile.get("gender", ""),
            str(profile.get("age", "")),
            profile.get("country_name", ""),
        )

    console.print(table)
    console.print(f"[dim]Total: {data.get('total', 0)} profiles[/dim]")
    
    # Display pagination links
    links = data.get('links', {})
    if links:
        console.print("\n[dim]Pagination:[/dim]")
        if links.get('self'):
            console.print(f"  [cyan]Current:[/cyan] {links['self']}")
        if links.get('next'):
            console.print(f"  [cyan]Next:[/cyan] {links['next']}")
        if links.get('prev'):
            console.print(f"  [cyan]Previous:[/cyan] {links['prev']}")


def get_profile(id: str = typer.Argument(..., help="Profile ID")):
    client = APIClient()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching profile...", total=None)
        response = client.get(f"/api/profiles/{id}")

    if response.status_code != 200:
        console.print(f"[red]Error fetching profile: {response.status_code}[/red]")
        console.print(response.text)
        raise typer.Exit(1)

    profile = response.json()

    table = Table(title="Profile Details")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="magenta")

    for key, value in profile.get("data", {}).items():
        table.add_row(key, str(value))

    console.print(table)


def search_profiles(query: str = typer.Argument(..., help="Search query")):
    client = APIClient()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Searching profiles...", total=None)
        response = client.get("/api/profiles/search", params={"q": query})

    if response.status_code != 200:
        console.print(f"[red]Error searching profiles: {response.status_code}[/red]")
        console.print(response.text)
        raise typer.Exit(1)

    data = response.json()

    table = Table(title=f"Search Results for: '{query}'")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="magenta")
    table.add_column("Gender", style="green")
    table.add_column("Age", style="yellow")
    table.add_column("Country", style="blue")

    for profile in data.get("data", []):
        table.add_row(
            str(profile.get("id", ""))[:8] + "...",
            profile.get("name", ""),
            profile.get("gender", ""),
            str(profile.get("age", "")),
            profile.get("country_name", ""),
        )

    console.print(table)
    console.print(f"[dim]Total: {data.get('total', 0)} profiles[/dim]")
    
    # Display pagination links
    links = data.get('links', {})
    if links:
        console.print("\n[dim]Pagination:[/dim]")
        if links.get('self'):
            console.print(f"  [cyan]Current:[/cyan] {links['self']}")
        if links.get('next'):
            console.print(f"  [cyan]Next:[/cyan] {links['next']}")
        if links.get('prev'):
            console.print(f"  [cyan]Previous:[/cyan] {links['prev']}")


def create_profile(name: str = typer.Argument(..., help="Profile name")):
    client = APIClient()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Creating profile...", total=None)
        response = client.post("/api/profiles", json={"name": name})

    if response.status_code == 201:
        console.print("[green]Profile created successfully![/green]")
        profile = response.json().get("data", {})
        console.print(f"[cyan]ID: {profile.get('id')}[/cyan]")
    elif response.status_code == 200:
        console.print("[yellow]Profile already exists.[/yellow]")
    else:
        console.print(f"[red]Error creating profile: {response.status_code}[/red]")
        console.print(response.text)
        raise typer.Exit(1)


def export_profiles(
    format: str = typer.Option("csv", "--format", "-f", help="Export format (csv)"),
    gender: Optional[str] = typer.Option(None, "--gender", "-g", help="Filter by gender"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Filter by country ID"),
    age_group: Optional[str] = typer.Option(None, "--age-group", help="Filter by age group"),
    min_age: Optional[int] = typer.Option(None, "--min-age", help="Minimum age"),
    max_age: Optional[int] = typer.Option(None, "--max-age", help="Maximum age"),
    sort_by: str = typer.Option("created_at", "--sort-by", "-s", help="Sort field"),
    order: str = typer.Option("asc", "--order", "-o", help="Sort order (asc/desc)"),
):
    if format != "csv":
        console.print("[red]Only CSV format is supported currently.[/red]")
        raise typer.Exit(1)

    client = APIClient()

    params = {
        "sortBy": sort_by,
        "order": order,
    }

    if gender:
        params["gender"] = gender
    if country:
        params["country_id"] = country
    if age_group:
        params["age_group"] = age_group
    if min_age:
        params["min_age"] = min_age
    if max_age:
        params["max_age"] = max_age

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Exporting profiles...", total=None)
        response = client.get("/api/profiles/export", params=params)

    if response.status_code != 200:
        console.print(f"[red]Error exporting profiles: {response.status_code}[/red]")
        console.print(response.text)
        raise typer.Exit(1)

    filename = f"profiles_{int(time.time())}.csv"
    with open(filename, "wb") as f:
        f.write(response.content)

    console.print(f"[green]Exported to {filename}[/green]")


def delete_profile(id: str = typer.Argument(..., help="Profile ID")):
    client = APIClient()

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Deleting profile...", total=None)
        response = client.delete(f"/api/profiles/{id}")

    if response.status_code == 204:
        console.print("[green]Profile deleted successfully![/green]")
    else:
        console.print(f"[red]Error deleting profile: {response.status_code}[/red]")
        console.print(response.text)
        raise typer.Exit(1)
