import json
import os
import base64
from pathlib import Path
from datetime import datetime, timedelta


class CredentialsManager:
    def __init__(self):
        self.credentials_dir = Path.home() / ".insighta"
        self.credentials_file = self.credentials_dir / "credentials.json"

    def ensure_credentials_dir(self):
        self.credentials_dir.mkdir(parents=True, exist_ok=True)

    def save_credentials(self, token_response):
        self.ensure_credentials_dir()
        access_token = token_response.get("access_token")
        user_info = self._decode_jwt(access_token)
        
        credentials = {
            "access_token": access_token,
            "refresh_token": token_response.get("refresh_token"),
            "expires_at": (datetime.now() + timedelta(minutes=3)).isoformat(),
            "username": user_info.get("username"),
            "role": user_info.get("role"),
        }
        with open(self.credentials_file, "w") as f:
            json.dump(credentials, f, indent=2)

    def load_credentials(self):
        if not self.credentials_file.exists():
            return None
        with open(self.credentials_file, "r") as f:
            return json.load(f)

    def is_logged_in(self):
        credentials = self.load_credentials()
        if not credentials:
            return False
        expires_at = datetime.fromisoformat(credentials.get("expires_at"))
        return datetime.now() < expires_at

    def clear_credentials(self):
        if self.credentials_file.exists():
            self.credentials_file.unlink()

    def get_access_token(self):
        credentials = self.load_credentials()
        if not credentials:
            return None
        return credentials.get("access_token")

    def get_refresh_token(self):
        credentials = self.load_credentials()
        if not credentials:
            return None
        return credentials.get("refresh_token")

    def get_user_info(self):
        credentials = self.load_credentials()
        if not credentials:
            return None
        
        # If credentials don't have username/role (old format), decode from token
        if not credentials.get("username") or not credentials.get("role"):
            access_token = credentials.get("access_token")
            if access_token:
                return self._decode_jwt(access_token)
        
        return {
            "username": credentials.get("username"),
            "role": credentials.get("role"),
        }

    def _decode_jwt(self, token):
        """Decode JWT token without verification to extract claims."""
        try:
            # Split token into parts
            parts = token.split(".")
            if len(parts) != 3:
                return {"username": "unknown", "role": "unknown"}
            
            # Decode payload (middle part)
            payload = parts[1]
            # Add padding if needed
            padding = 4 - len(payload) % 4
            if padding != 4:
                payload += "=" * padding
            
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)
            
            return {
                "username": claims.get("sub", "unknown"),
                "role": claims.get("role", "unknown"),
            }
        except Exception:
            return {"username": "unknown", "role": "unknown"}
