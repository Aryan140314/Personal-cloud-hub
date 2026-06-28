# Personal Cloud Hub

Personal Cloud Hub is a PyQt6 desktop application that organizes local files, backs them up to Google Drive, and maintains a fully searchable SQLite record of every upload. It supports manual file selection, drag-and-drop uploads, recursive folder monitoring, SHA-256 duplicate detection with configurable policies (skip, rename, overwrite), optional local backup copies, Google Drive deletion, CSV data export, desktop notifications, structured rotating-file logging, and interactive analytics charts.

The app was built around the brief in `Project Objective.pdf`.

---

## Features

### Core Functionality
- **Google Drive backup** — Files are uploaded into a dedicated root folder on Drive, organized by category (e.g. `My Drive / Personal Cloud Hub / Documents`).
- **SHA-256 duplicate detection** — Each file is hashed before upload; duplicates are handled according to the configured policy (`skip`, `rename`, or `overwrite`).
- **Automatic file classification** — Files are sorted into categories (Documents, Coding, Images, Archives, Certificates, Projects, Other) based on their extension.
- **Folder monitoring** — Uses `watchdog` to recursively watch configured folders and auto-upload new or moved files. A file-stability check prevents uploading incomplete writes.
- **Concurrent uploads** — A `ThreadPoolExecutor` (4 workers) processes manual and drag-and-drop uploads in the background, keeping the UI responsive.
- **Retry pending uploads** — Files that couldn't be uploaded because Google Drive wasn't set up yet can be retried in bulk once credentials are configured.
- **Delete from Google Drive** — Move uploaded files to Google Drive's trash directly from the Search page.
- **CSV export** — Export all file records to CSV from both the Search page and the Analytics page.
- **Optional local backup** — Copies uploaded files to a local folder organized by category.
- **Desktop notifications** — Uses `plyer` to show native OS notifications on upload success or failure (can be toggled off).
- **Structured logging** — Rotating log files (5 MB per file, 3 backups) with timestamped, leveled output to both `logs/app.log` and the console.

### User Interface
- **Dashboard** — Live overview with metric cards for total files, storage used, uploads today, failed uploads, pending uploads, and Drive connection status. Includes a recent-activity table.
- **Upload Center** — Drag-and-drop zone, file picker, folder monitor toggle, retry button, real-time progress indicator, watched-folder list, and a scrollable upload log table.
- **Search** — Full-text search across filename, path, category, file type, and status. Action buttons to open local files, open Drive links, delete from Drive, and export to CSV.
- **Analytics** — Uploads-per-day line chart and file-type distribution bar chart powered by `pyqtgraph`, plus a summary table.
- **Settings** — Watch folders, Drive root folder name, local backup folder, duplicate policy, theme selector (dark / light), auto-start monitor toggle, and notifications toggle.
- **Dark and light themes** — Custom stylesheets with card-based UI, sidebar navigation, and accent colours.
- **Status bar** — Persistent bar at the bottom showing file counts, monitor status, and Drive connection status. Refreshes every 5 seconds.

---

## Tech Stack

| Layer | Technology |
| --- | --- |
| Language | Python 3 (3.10+ recommended) |
| Desktop UI | PyQt6 |
| Local database | SQLite (via `sqlite3`) |
| Google Drive API | PyDrive2 |
| Folder monitoring | watchdog |
| Analytics charts | pyqtgraph |
| Desktop notifications | plyer |
| Environment config | python-dotenv |

---

## Project Structure

```text
personal_cloud_hub/
├── app.py                         # Entry point — creates folders, initialises DB & services, launches UI
├── get_token.py                   # Standalone helper to generate/refresh Google Drive OAuth tokens
├── requirements.txt               # Python dependencies
├── launch_personal_cloud_hub.bat  # Windows launcher (creates venv, installs deps, runs app)
├── Project Objective.pdf          # Original project brief
├── README.md
├── .gitignore
│
├── assets/
│   ├── icons/
│   └── images/
│
├── config/
│   ├── credentials.json           # (gitignored) Google OAuth client — you create this
│   ├── token.json                 # (gitignored) Saved OAuth token — auto-generated
│   ├── pydrive_settings.yaml      # (gitignored) PyDrive2 settings — auto-generated
│   └── settings.json              # Default application settings (JSON)
│
├── database/
│   └── files.db                   # (gitignored) SQLite database — auto-created at first launch
│
├── logs/
│   └── app.log                    # (gitignored) Rotating application log
│
├── services/
│   ├── __init__.py
│   ├── database_service.py        # Thread-safe SQLite wrapper — schema, queries, settings, export
│   ├── drive_service.py           # Google Drive connection, upload, delete, folder management
│   ├── file_classifier.py         # Extension-based file categorisation
│   ├── logging_config.py          # Rotating file + console logging setup
│   ├── monitor_service.py         # watchdog-based folder watcher with stability checks
│   ├── notification_service.py    # Desktop notification bridge via plyer
│   └── upload_service.py          # Upload pipeline — hashing, duplicate policy, Drive upload, retry, delete
│
└── ui/
    ├── __init__.py
    ├── analytics_page.py          # Charts + summary table + CSV export
    ├── dashboard.py               # Metric cards + recent-activity table + main window + status bar
    ├── search_page.py             # Search table + open / Drive link / delete / CSV export
    ├── settings_page.py           # All user-configurable preferences
    ├── theme.py                   # Dark and light QSS stylesheets
    ├── upload_page.py             # Drop zone + file picker + monitor + retry + upload log
    └── widgets.py                 # Reusable components — MetricCard, page_header, row_widget, format_bytes
```

---

## How It Works

1. **Startup** — `app.py` ensures required directories exist, sets up rotating-file logging via `logging_config.py`, initialises the SQLite database schema and default settings, creates all service instances, and launches the PyQt6 main window.

2. **Uploading** — Users upload files by clicking **Select Files**, dragging files/folders into the drop zone, or starting the folder monitor. All upload methods run asynchronously using a thread pool.

3. **Upload pipeline** (`UploadService`) — For each file:
   - Validate that the file exists.
   - Compute its SHA-256 hash.
   - Classify the file into a category.
   - Check for duplicates and apply the configured policy (`skip` / `rename` / `overwrite`).
   - Create a `pending` database record.
   - Optionally copy the file to the local backup folder.
   - Upload to Google Drive via `DriveService`.
   - Update the database with the Drive ID, link, and `uploaded` status.
   - Send a desktop notification.

4. **Google Drive** (`DriveService`) — Connects using PyDrive2 OAuth, creates the app root folder and category subfolders on demand, caches folder IDs at runtime, and supports upload, delete (trash), and reconnection.

5. **Folder monitoring** (`MonitorService`) — Uses `watchdog` to detect new and moved files in watched folders. Files are debounced and stability-checked (file size must stop changing) before being queued for upload.

6. **Data persistence** — All file metadata, upload logs, and settings are stored in `database/files.db`. The Search and Analytics pages query this database directly.

---

## File Categories

Files are categorized by extension in `services/file_classifier.py`.

| Category | Extensions |
| --- | --- |
| Documents | `.pdf`, `.doc`, `.docx`, `.ppt`, `.pptx`, `.xls`, `.xlsx`, `.txt`, `.md` |
| Coding | `.py`, `.java`, `.js`, `.ts`, `.jsx`, `.tsx`, `.html`, `.css`, `.cpp`, `.c`, `.cs`, `.go`, `.rs`, `.php`, `.rb`, `.json`, `.xml`, `.yaml`, `.yml`, `.sql` |
| Images | `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp`, `.tiff`, `.svg` |
| Archives | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.bz2` |
| Certificates | `.cer`, `.crt`, `.pem`, `.pfx`, `.p12`, or filenames containing `certificate` / `certification` |
| Projects | `.ipynb`, `.fig`, `.psd`, `.ai`, `.blend` |
| Other | Everything else |

---

## Upload Statuses

| Status | Meaning |
| --- | --- |
| `pending` | Record created, waiting for Drive upload to start. |
| `uploaded` | Successfully uploaded to Google Drive. |
| `duplicate` | Hash matched an already-uploaded file; handled per duplicate policy. |
| `pending_setup` | Waiting for Google Drive credentials (`config/credentials.json` missing or invalid). |
| `failed` | Upload failed after processing started. |
| `deleted` | File was moved to Google Drive trash via the app. |
| `backup_warning` | Local backup copy failed (logged only; does not stop the upload pipeline). |

---

## Duplicate Policies

Configurable from the Settings page. Stored in the database as `duplicate_policy`.

| Policy | Behaviour |
| --- | --- |
| `skip` (default) | Create a `duplicate` record and skip the upload. Links back to the original Drive file. |
| `rename` | Upload a copy with a timestamped filename (e.g. `report_20260628_171000.pdf`). |
| `overwrite` | Trash the old file on Drive and upload the new version. |

---

## Requirements

- Windows, macOS, or Linux with Python installed.
- Python 3.10 or newer is recommended.
- A Google account if you want Google Drive uploads.
- Google Drive API OAuth credentials saved as `config/credentials.json`.

**Dependencies** (`requirements.txt`):

```text
PyQt6>=6.7
watchdog>=4.0
PyDrive2>=1.19
sqlite-utils>=3.36
plyer>=2.1
pyqtgraph>=0.13
python-dotenv>=1.0
```

---

## Run Locally

```powershell
# 1. Create and activate a virtual environment
python -m venv venv
.\venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the app
python app.py
```

On first launch, the app creates any missing project folders and initialises the SQLite database at `database/files.db`.

---

## Run With The Windows Launcher

Double-click `launch_personal_cloud_hub.bat`. The launcher:

1. Moves into the project directory.
2. Creates `venv` if it does not exist.
3. Installs `requirements.txt` once (writes a sentinel file to skip on subsequent runs).
4. Starts `app.py` using the virtual-environment Python.

---

## Google Drive Setup

The app does not generate Google OAuth credentials automatically. You must create a desktop OAuth client in Google Cloud Console.

### Step-by-step

1. Open the [Google Drive Python quickstart](https://developers.google.com/workspace/drive/api/quickstart/python).
2. Create or choose a Google Cloud project.
3. Enable the **Google Drive API**.
4. Configure the **OAuth consent screen** (set publishing status to Testing and add your email as a test user).
5. Create an **OAuth client** with application type **Desktop app**.
6. Download the OAuth client JSON file.
7. Rename it to `credentials.json` and save it at:

   ```text
   config/credentials.json
   ```

8. Run the app and upload a file. The first connection opens a browser for Google login.

After successful authorization, the token is saved at `config/token.json` and PyDrive2 settings are auto-generated at `config/pydrive_settings.yaml`.

### Token Helper Script

If you need to generate or refresh your token outside the app (e.g. on first setup or after token expiry), run:

```powershell
python get_token.py
```

This script:

1. Verifies that `config/credentials.json` exists.
2. Deletes any old `config/token.json`.
3. Writes fresh PyDrive2 settings.
4. Opens a browser for Google OAuth login.
5. Saves the new token and verifies the connection.

---

## Google Drive Destination

By default, uploaded files are stored under:

```text
My Drive / Personal Cloud Hub / <Category>
```

Examples:

```text
My Drive / Personal Cloud Hub / Documents
My Drive / Personal Cloud Hub / Coding
My Drive / Personal Cloud Hub / Images
My Drive / Personal Cloud Hub / Archives
My Drive / Personal Cloud Hub / Certificates
My Drive / Personal Cloud Hub / Projects
My Drive / Personal Cloud Hub / Other
```

The root folder name can be changed from the Settings page. The new name is saved in SQLite under the `google_drive_root` setting.

---

## Using The App

### Dashboard

The Dashboard shows six metric cards:

- **Total Files** — All tracked file records.
- **Storage Used** — Sum of file sizes for successfully uploaded files.
- **Uploads Today** — Number of files uploaded today.
- **Failed Uploads** — Records with `failed` status.
- **Pending** — Records with `pending` or `pending_setup` status.
- **Drive Status** — Current Google Drive connection state.

Below the cards is a **Recent Activity** table showing the latest 12 file records with filename, category, size, status, and last-updated timestamp.

The dashboard refreshes automatically every 5 seconds (only when visible).

### Upload Center

Three upload methods:

- **Select Files** — Opens a native file picker. Selected files are uploaded concurrently.
- **Drag and Drop** — Drag files or folders onto the drop zone. Folders are expanded recursively. Batches of 10+ files prompt a confirmation dialog.
- **Folder Monitor** — Toggle the `watchdog` monitor to watch all configured folders recursively. New and moved files are uploaded automatically after a stability check.

Additional controls:

- **Retry Pending** — Retries all `pending_setup` records (prompts for confirmation first).
- **Progress indicator** — Shows completed / queued count and failures.
- **Upload Logs** — Scrollable table of the 80 most recent log entries with timestamp, filename, status, and message.
- **Watched Folders** — List of currently configured watch folders.
- **Drive destination** — Shows the current upload target path on Google Drive.

### Search

- **Full-text search** across filename, file path, category, file type, and status.
- **Results table** with columns: File, Category, Type, Size, Status, Path, and Drive availability.
- **Action buttons**:
  - **Open Local File** — Opens the file using the OS default application.
  - **Open Drive Link** — Opens the Google Drive link in a browser.
  - **Delete from Drive** — Moves the file to Google Drive trash (with confirmation dialog; can be recovered from Drive trash).
  - **Export to CSV** — Saves all file records (not just search results) to a CSV file.

### Analytics

- **Uploads Per Day** — Line chart (pyqtgraph) showing daily upload counts for the last 7 days.
- **File Types** — Bar chart showing the distribution of file types.
- **Summary Table** — Total files, uploaded files, pending uploads, and failed uploads.
- **Export to CSV** — Export all file records to a CSV file.

### Settings

| Setting | Description |
| --- | --- |
| Watch Folders | Add/remove folders for the folder monitor. Non-existent folders are removed on save. |
| Google Drive Root Folder | Name of the root folder on Google Drive (default: `Personal Cloud Hub`). |
| Local Backup Folder | Optional folder where uploaded files are copied locally, organized by category. |
| Duplicate File Policy | `skip` (default), `rename`, or `overwrite`. |
| Theme | `dark` or `light`. Applied immediately on save. |
| Auto-start Monitor | Automatically start the folder monitor when the app launches. |
| Desktop Notifications | Toggle OS-level upload notifications. |

Settings are persisted in the SQLite database. A save confirmation message is shown after each save.

---

## Local Backup Folder

If configured in Settings, each uploaded file is copied to:

```text
<backup folder> / <Category> / <filename>
```

This is independent of Google Drive. If the local copy fails, the app records a `backup_warning` log entry but the upload pipeline continues normally.

---

## Database

The SQLite database is created at `database/files.db` and contains three tables plus performance indexes.

### `files`

| Column | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | Primary key (auto-increment) |
| `filename` | TEXT | File name |
| `filepath` | TEXT | Full local path |
| `filesize` | INTEGER | File size in bytes |
| `filetype` | TEXT | File extension (lowercase, no dot) |
| `category` | TEXT | Classified category |
| `file_hash` | TEXT | SHA-256 hash |
| `upload_date` | TEXT | ISO-8601 upload timestamp |
| `google_drive_id` | TEXT | Drive file ID |
| `google_drive_link` | TEXT | Drive web link |
| `status` | TEXT | Current status |
| `message` | TEXT | Human-readable status message |
| `created_at` | TEXT | Record creation timestamp |
| `updated_at` | TEXT | Last update timestamp |

**Indexes**: `idx_files_filename`, `idx_files_hash`, `idx_files_status`, `idx_files_upload_date`.

### `settings`

Key-value store for application preferences. Values are JSON-serialized. Uses `ON CONFLICT` upsert.

| Key | Default |
| --- | --- |
| `watch_folders` | `[]` |
| `theme` | `"dark"` |
| `notifications` | `true` |
| `auto_start_monitor` | `false` |
| `google_drive_root` | `"Personal Cloud Hub"` |
| `backup_folder` | `""` |
| `duplicate_policy` | `"skip"` |

### `upload_logs`

| Column | Type | Description |
| --- | --- | --- |
| `id` | INTEGER | Primary key (auto-increment) |
| `filename` | TEXT | File name |
| `upload_time` | TEXT | ISO-8601 timestamp |
| `status` | TEXT | Result status |
| `message` | TEXT | Descriptive message |

---

## Logging

The app uses Python's `logging` module configured by `services/logging_config.py`:

- **Rotating file handler** — Writes to `logs/app.log`, rotates at 5 MB, keeps 3 backups.
- **Console handler** — Outputs to `stdout` for development.
- **Format**: `2026-06-28 17:10:28 | INFO     | services.drive_service | Connected to Google Drive successfully.`

All services use module-level loggers (`logging.getLogger(__name__)`) for clear source identification.

---

## Configuration Files

| File | Purpose | In Git? |
| --- | --- | --- |
| `config/settings.json` | Readable default settings | ✅ Yes |
| `config/credentials.json` | Google OAuth client secret | ❌ No |
| `config/token.json` | Saved OAuth token | ❌ No |
| `config/pydrive_settings.yaml` | PyDrive2 runtime config | ❌ No |
| `database/files.db` | SQLite database | ❌ No |
| `logs/app.log` | Application log | ❌ No |

Runtime settings are stored in SQLite after the app initializes. The JSON file provides readable defaults, while the database is the source of truth during app usage.

---

## Troubleshooting

### Google Drive setup required

Make sure `config/credentials.json` exists. If the token is expired or corrupt, run:

```powershell
python get_token.py
```

### PyDrive2 is not installed

```powershell
pip install -r requirements.txt
```

If using the Windows launcher, delete `venv\.personal_cloud_hub_ready` and run the launcher again.

### No valid watch folders configured

Open Settings, add at least one existing folder, save, then return to Upload Center and start the monitor.

### Analytics charts do not appear

Reinstall dependencies — the charts require `pyqtgraph`:

```powershell
pip install -r requirements.txt
```

### Desktop notifications do not appear

Confirm notifications are enabled in Settings and that the OS allows app notifications. Uploads still work if notifications fail.

### Token expired or "invalid_grant" error

Run `python get_token.py` to delete the old token and re-authenticate through the browser.

---

## Architecture & Design Notes

- **Thread safety** — `DatabaseService` uses a `threading.Lock` to serialize all SQLite connections. Each operation acquires the lock, opens a connection, commits, closes, and releases.
- **Concurrent uploads** — `UploadPage` uses a `ThreadPoolExecutor` (4 workers) so multiple files upload simultaneously without freezing the UI.
- **Signal bridge** — Upload results from background threads are delivered to the UI via `pyqtSignal` (`UploadSignals.completed`), ensuring thread-safe Qt updates.
- **Smart refresh** — The 5-second timer only refreshes the currently visible page to minimize CPU and database usage.
- **Folder cache** — `DriveService` caches root and category folder IDs at runtime to avoid repeated Google Drive API lookups.
- **File stability check** — `MonitorService` waits for a file's size to stabilize (up to 10 checks, 750ms apart) before uploading, preventing uploads of partially-written files.
- **Debouncing** — Recently-seen file paths are tracked with a 3-second cooldown and a 30-second expiry to prevent duplicate upload triggers.
- **Graceful shutdown** — `MainWindow.closeEvent` stops the folder monitor before closing.
- **Dynamic PyDrive2 config** — OAuth settings YAML is generated programmatically from the paths to `credentials.json` and `token.json`.

---

## Git Hygiene

The repository ignores local runtime and credential files through `.gitignore`:

```text
venv/
.venv/
__pycache__/
*.pyc
database/*.db
logs/*.log
config/credentials.json
config/token.json
config/pydrive_settings.yaml
```

**Do not commit** personal Google credentials, OAuth tokens, local databases, or virtual environments.

---

## License

This project is for personal and educational use.
