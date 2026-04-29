# Insighta Labs+ CLI

A command-line interface for interacting with the Insighta Labs+ backend API.

## Installation

```bash
pip install -e .
```

## Configuration

Set the following environment variables:

```bash
export INSIGHTA_BACKEND_URL="http://localhost:8080"
export GITHUB_CLIENT_ID="your_github_client_id"
```

Or use command-line options:

```bash
insighta login --backend-url http://localhost:8080 --client-id your_client_id
```

## Usage

### Authentication

```bash
insighta login
insighta logout
insighta whoami
```

After successful login, the CLI displays your username and role (admin or analyst).

### Profiles

```bash
insighta profiles list
insighta profiles list --gender male
insighta profiles list --country NG --age-group adult
insighta profiles list --min-age 25 --max-age 40
insighta profiles list --sort-by age --order desc
insighta profiles list --page 2 --limit 20

insighta profiles get <id>

insighta profiles search "young males from nigeria"

insighta profiles create --name "Harriet Tubman"

insighta profiles delete <id>

insighta profiles export --format csv
insighta profiles export --format csv --gender male --country NG
```

## Role-Based Access Control

The CLI enforces role-based permissions:

- **Admin**: Full access - can create, delete, list, search, and export profiles
- **Analyst**: Read-only access - can list, search, get, and export profiles

Attempting to perform admin-only actions (create, delete) as an analyst will result in an access denied error.

## Credentials

Tokens are stored at `~/.insighta/credentials.json`.

- **Access tokens**: Expire after 3 minutes
- **Refresh tokens**: Expire after 5 minutes

The CLI automatically attempts to refresh tokens when they expire. If refresh fails, you'll be prompted to log in again.

## PKCE Flow

The CLI implements the PKCE (Proof Key for Code Exchange) flow for secure OAuth authentication:

1. Generates a random `code_verifier` and `code_challenge`
2. Opens GitHub OAuth in the browser
3. Starts a local callback server on port 8080
4. Captures the authorization code
5. Exchanges the code for access and refresh tokens

## Error Handling

The CLI provides clear error messages for common issues:

- **401 Unauthorized**: Token expired or invalid (auto-refresh attempted)
- **403 Forbidden**: Access denied due to insufficient permissions
- **400 Bad Request**: Invalid parameters or missing API version header
- **429 Too Many Requests**: Rate limit exceeded

## Pagination

List and search commands display pagination links:

```
Pagination:
  Current: /api/profiles?page=1&limit=10
  Next: /api/profiles?page=2&limit=10
  Previous: /api/profiles?page=1&limit=10
```
# Insightia_cli
