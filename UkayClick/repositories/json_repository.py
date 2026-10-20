import hashlib
import json
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
USERS_FILE = DATA_DIR / "users.json"
LEGACY_MIGRATION_MARKER = DATA_DIR / ".legacy_data_assigned"
DATA_NAMES = ("inventory", "transactions", "expenses")
_current_user = None


def _safe_user_key(username):
    # A stable, filesystem-safe identifier without exposing raw usernames in paths.
    normalized = str(username or "").strip().casefold()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def _user_data_dir(username=None):
    username = username if username is not None else _current_user
    if not username:
        # Keep safe behavior for calls made before login; app data operations should
        # always set a current user first.
        return DATA_DIR / "unassigned"
    return DATA_DIR / "accounts" / _safe_user_key(username)


def set_current_user(username):
    """Select the account whose inventory, sales, and expenses are active."""
    global _current_user
    _current_user = str(username or "").strip() or None
    if not _current_user:
        return

    account_dir = _user_data_dir(_current_user)
    account_dir.mkdir(parents=True, exist_ok=True)

    # Preserve existing prototype data by assigning the old shared data to the
    # first account that signs in after this update. Later accounts start clean.
    if not LEGACY_MIGRATION_MARKER.exists():
        for name in DATA_NAMES:
            legacy_path = DATA_DIR / f"{name}.json"
            account_path = account_dir / f"{name}.json"
            if not account_path.exists() and legacy_path.exists():
                try:
                    content = json.loads(legacy_path.read_text(encoding="utf-8"))
                    account_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
                except (json.JSONDecodeError, OSError):
                    pass
        LEGACY_MIGRATION_MARKER.write_text(_current_user, encoding="utf-8")


def _read_users():
    if not USERS_FILE.exists():
        return []
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write_users(data):
    USERS_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _read(name):
    path = _user_data_dir() / f"{name}.json"
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write(name, data):
    path = _user_data_dir() / f"{name}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_users(): return _read_users()
def save_users(data): _write_users(data)
def load_inventory(): return _read("inventory")
def save_inventory(data): _write("inventory", data)
def load_transactions(): return _read("transactions")
def save_transactions(data): _write("transactions", data)
def load_expenses(): return _read("expenses")
def save_expenses(data): _write("expenses", data)
def timestamp(): return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
