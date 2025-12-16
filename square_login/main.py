# ABOUTME: CLI entry point for Square login cookie capture.
# ABOUTME: Opens browser with pydoll, waits for login, uploads cookies to server.

import asyncio

import click
import httpx
from pydoll.browser.chromium import Chrome
from pydoll.browser.options import ChromiumOptions

SQUARE_LOGIN_URL = "https://app.squareup.com/login"


async def capture_login_cookies() -> list[dict]:
    """Open browser, wait for Square login, return cookies."""
    options = ChromiumOptions()
    options.headless = False  # User needs to see browser to log in

    cookies = []

    async with Chrome(options=options) as browser:
        tab = await browser.start()

        click.echo("Navigating to Square login...")
        await tab.go_to(SQUARE_LOGIN_URL)

        click.echo("Waiting for login... (close browser to cancel)")
        click.echo()

        # Poll for successful login
        max_wait = 300  # 5 minutes max
        for _ in range(max_wait):
            await asyncio.sleep(1)

            try:
                current_url = await tab.current_url
            except Exception:
                # Browser was closed
                click.echo("Browser was closed - aborting.")
                return []

            # Success: redirected away from login page
            if "/login" not in current_url and "squareup.com" in current_url:
                click.echo(f"Login detected! Current URL: {current_url}")
                break
        else:
            click.echo("Timeout waiting for login (5 minutes)")
            return []

        # Get cookies using pydoll's built-in method
        try:
            raw_cookies = await tab.get_cookies()

            # Keep full cookie data including expiration
            for c in raw_cookies:
                cookie = {
                    "name": c.get("name"),
                    "value": c.get("value"),
                    "domain": c.get("domain"),
                    "path": c.get("path", "/"),
                }
                # Include expiration if present (Unix timestamp)
                if "expires" in c:
                    cookie["expires"] = c["expires"]
                # Include other useful fields
                if "httpOnly" in c:
                    cookie["httpOnly"] = c["httpOnly"]
                if "secure" in c:
                    cookie["secure"] = c["secure"]
                cookies.append(cookie)
        except Exception as e:
            click.echo(f"Error getting cookies: {e}")
            return []

    return cookies


@click.command()
@click.option("--server", required=True, help="Arpias server URL (e.g., https://arpias.example.com)")
@click.option("--token", required=True, help="One-time upload token from the admin page")
def main(server: str, token: str):
    """
    Open Square login in a browser, capture session cookies, and upload to the Arpias server.

    Usage:
        uvx arpias-square-helper --server https://arpias.example.com --token YOUR_TOKEN
    """
    # Normalize server URL
    server = server.rstrip("/")

    click.echo("Square Session Capture Tool")
    click.echo("=" * 40)
    click.echo(f"Server: {server}")
    click.echo()

    click.echo("Opening browser - please log in to Square...")
    click.echo("The browser will close automatically when login is detected.")
    click.echo()

    # Run async capture
    cookies = asyncio.run(capture_login_cookies())

    if not cookies:
        click.echo("No cookies captured - login may have failed.")
        return

    click.echo(f"Captured {len(cookies)} cookies")

    # Upload cookies to server
    click.echo()
    click.echo(f"Uploading cookies to {server}...")

    try:
        response = httpx.post(
            f"{server}/api/session/upload",
            json={"token": token, "cookies": cookies},
            timeout=30.0,
        )

        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                click.echo()
                click.echo("Session uploaded successfully!")
                click.echo("You can now close this terminal.")
            else:
                click.echo(f"Upload failed: {data.get('error', 'Unknown error')}")
        else:
            click.echo(f"Upload failed with status {response.status_code}")
            try:
                error_data = response.json()
                click.echo(f"Error: {error_data.get('error', response.text)}")
            except Exception:
                click.echo(f"Response: {response.text[:500]}")

    except httpx.ConnectError:
        click.echo(f"Could not connect to server at {server}")
        click.echo("Please check the server URL and try again.")
    except Exception as e:
        click.echo(f"Upload error: {e}")


if __name__ == "__main__":
    main()
