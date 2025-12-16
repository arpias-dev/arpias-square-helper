# Square Login

CLI tool to capture Square session cookies and upload them to an Arpias server.

## Usage

Run directly with uvx (no installation needed):

```bash
uvx --from git+https://github.com/arpias-dev/square-login.git square-login \
    --server https://your-arpias-server.com \
    --token YOUR_UPLOAD_TOKEN
```

## How It Works

1. Opens a browser window to the Square login page
2. You log in manually (handles 2FA, Cloudflare protection, etc.)
3. Once logged in, the tool captures your session cookies
4. Cookies are securely uploaded to your Arpias server using the one-time token

## Getting a Token

1. Go to your Arpias server's admin page: `/admin/session`
2. Click "Generate Upload Token"
3. Copy the displayed command and run it in your terminal

## Requirements

- Python 3.10+
- Playwright browsers (installed automatically on first run)
