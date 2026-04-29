import os
import requests
from rich.console import Console

from insighta.config.credentials import CredentialsManager

console = Console()


class APIClient:
    def __init__(self, backend_url=None):
        self.backend_url = backend_url or os.getenv("INSIGHTA_BACKEND_URL", "http://localhost:8080")
        self.credentials_manager = CredentialsManager()

    def _get_headers(self):
        access_token = self.credentials_manager.get_access_token()
        if not access_token:
            console.print("[red]Not authenticated. Please run 'insighta login'.[/red]")
            raise Exception("Not authenticated")
        return {
            "Authorization": f"Bearer {access_token}",
            "X-API-Version": "1",
        }

    def _refresh_token(self):
        refresh_token = self.credentials_manager.get_refresh_token()
        if not refresh_token:
            raise Exception("No refresh token available")

        response = requests.post(
            f"{self.backend_url}/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        if response.status_code == 200:
            self.credentials_manager.save_credentials(response.json())
            return True
        return False

    def request(self, method, endpoint, **kwargs):
        headers = self._get_headers()
        url = f"{self.backend_url}{endpoint}"
        response = requests.request(method, url, headers=headers, **kwargs)

        if response.status_code == 401:
            console.print("[yellow]Token expired, attempting refresh...[/yellow]")
            if self._refresh_token():
                headers = self._get_headers()
                response = requests.request(method, url, headers=headers, **kwargs)
            else:
                console.print("[red]Token refresh failed. Please run 'insighta login'.[/red]")
                raise Exception("Authentication failed")

        if response.status_code == 403:
            try:
                error_data = response.json()
                message = error_data.get("message", "Access denied")
                console.print(f"[red]Access denied: {message}[/red]")
            except:
                console.print("[red]Access denied. This action may require admin role.[/red]")
            raise Exception("Access denied")

        if response.status_code == 400:
            try:
                error_data = response.json()
                message = error_data.get("message", "Bad request")
                console.print(f"[red]Bad request: {message}[/red]")
            except:
                console.print("[red]Bad request. Check your input parameters.[/red]")
            raise Exception("Bad request")

        if response.status_code == 429:
            console.print("[red]Rate limit exceeded. Please wait before trying again.[/red]")
            raise Exception("Rate limit exceeded")

        return response

    def get(self, endpoint, **kwargs):
        return self.request("GET", endpoint, **kwargs)

    def post(self, endpoint, **kwargs):
        return self.request("POST", endpoint, **kwargs)

    def delete(self, endpoint, **kwargs):
        return self.request("DELETE", endpoint, **kwargs)
