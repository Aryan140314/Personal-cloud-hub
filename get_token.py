"""Run this script to get a fresh Google Drive OAuth token.

It opens a browser window for Google login and saves the new token
to config/token.json.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = BASE_DIR / "config"
CREDENTIALS = CONFIG_DIR / "credentials.json"
TOKEN = CONFIG_DIR / "token.json"
SETTINGS = CONFIG_DIR / "pydrive_settings.yaml"

# Step 1 — Make sure credentials.json exists.
if not CREDENTIALS.exists():
    print("ERROR: config/credentials.json not found.")
    print("Download it from Google Cloud Console → APIs & Services → Credentials.")
    raise SystemExit(1)

# Step 2 — Delete old token if it exists.
if TOKEN.exists():
    TOKEN.unlink()
    print("Deleted old token.json")

# Step 3 — Write fresh PyDrive2 settings.
cred_path = CREDENTIALS.as_posix().replace("'", "''")
tok_path = TOKEN.as_posix().replace("'", "''")
SETTINGS.write_text(f"""client_config_backend: file
client_config_file: '{cred_path}'
save_credentials: true
save_credentials_backend: file
save_credentials_file: '{tok_path}'
get_refresh_token: true
oauth_scope:
  - https://www.googleapis.com/auth/drive.file
""", encoding="utf-8")
print("Wrote fresh pydrive_settings.yaml")

# Step 4 — Run OAuth flow.
try:
    from pydrive2.auth import GoogleAuth
    from pydrive2.drive import GoogleDrive
except ImportError:
    print("ERROR: PyDrive2 not installed. Run: pip install pydrive2")
    raise SystemExit(1)

print("\nOpening browser for Google login...")
print("If the browser does not open, copy the URL from the terminal.\n")

gauth = GoogleAuth(settings_file=str(SETTINGS))
gauth.LocalWebserverAuth()
gauth.SaveCredentialsFile(str(TOKEN))

# Step 5 — Verify.
drive = GoogleDrive(gauth)
about = drive.GetAbout()
print(f"\n✅ Success! Connected as: {about['user']['displayName']}")
print(f"   Email: {about['user']['emailAddress']}")
print(f"   Token saved to: {TOKEN}")
print("\nYou can now close this terminal and run the app normally.")
