# Login credentials from environment variables.
# Set VOTER_APP_USERNAME and VOTER_APP_PASSWORD in .env or your environment.
# Copy .env.example to .env and fill in your values.

import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv optional; use system env vars

USERNAME = (os.environ.get("VOTER_APP_USERNAME") or "").strip()
PASSWORD = (os.environ.get("VOTER_APP_PASSWORD") or "").strip()
