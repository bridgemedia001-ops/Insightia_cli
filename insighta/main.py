import typer
from rich.console import Console

from insighta.auth import commands as auth_commands
from insighta.profiles import commands as profile_commands

app = typer.Typer(help="Insighta Labs+ CLI")
console = Console()

profiles_app = typer.Typer(help="Profile management commands")

profiles_app.command(name="list")(profile_commands.list_profiles)
profiles_app.command(name="get")(profile_commands.get_profile)
profiles_app.command(name="search")(profile_commands.search_profiles)
profiles_app.command(name="create")(profile_commands.create_profile)
profiles_app.command(name="export")(profile_commands.export_profiles)
profiles_app.command(name="delete")(profile_commands.delete_profile)

app.add_typer(profiles_app, name="profiles")

app.command(name="login")(auth_commands.login)
app.command(name="logout")(auth_commands.logout)
app.command(name="whoami")(auth_commands.whoami)


if __name__ == "__main__":
    app()
