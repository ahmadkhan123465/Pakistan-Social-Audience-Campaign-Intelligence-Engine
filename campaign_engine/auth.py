"""Authentication, user management, CSRF protection, and security audit logging.

Stored in a dedicated SQLite database (`data/auth.db`) isolated from `data/campaign.db`
so that the read-only SQL Console can never expose credentials or personal user data,
and rebuilding the analytics database never wipes registered user accounts.
"""
from __future__ import annotations

import hmac
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Tuple
from urllib.parse import urlparse

from werkzeug.security import check_password_hash, generate_password_hash

from . import config

AUTH_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS user (
    user_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username        TEXT NOT NULL UNIQUE COLLATE NOCASE,
    email           TEXT NOT NULL UNIQUE COLLATE NOCASE,
    full_name       TEXT NOT NULL,
    password_hash   TEXT NOT NULL,
    role            TEXT NOT NULL DEFAULT 'analyst' CHECK (role IN ('admin','analyst','viewer')),
    is_active       INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0,1)),
    failed_attempts INTEGER NOT NULL DEFAULT 0,
    locked_until    TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    last_login_at   TEXT
);

CREATE TABLE IF NOT EXISTS auth_audit_log (
    log_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER REFERENCES user(user_id) ON DELETE SET NULL,
    username    TEXT,
    event_type  TEXT NOT NULL,
    ip_address  TEXT,
    user_agent  TEXT,
    details     TEXT,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS ix_audit_user ON auth_audit_log(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_audit_time ON auth_audit_log(created_at DESC);

CREATE TABLE IF NOT EXISTS user_consent (
    consent_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL UNIQUE REFERENCES user(user_id) ON DELETE CASCADE,
    decision        TEXT NOT NULL CHECK (decision IN ('accepted_all','rejected_all','custom')),
    essential       INTEGER NOT NULL DEFAULT 1 CHECK (essential IN (0,1)),
    analytics       INTEGER NOT NULL DEFAULT 0 CHECK (analytics IN (0,1)),
    personalization INTEGER NOT NULL DEFAULT 0 CHECK (personalization IN (0,1)),
    diagnostics     INTEGER NOT NULL DEFAULT 0 CHECK (diagnostics IN (0,1)),
    reason          TEXT NOT NULL DEFAULT '',
    updated_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
"""

_USERNAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{2,29}$")
_EMAIL_RE = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_PW_METHOD = "pbkdf2:sha256:260000"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: Optional[datetime] = None) -> str:
    return (dt or _utc_now()).strftime("%Y-%m-%d %H:%M:%S")


def _parse_utc(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def connect_auth(path: Optional[Path] = None) -> sqlite3.Connection:
    db_path = Path(path or config.AUTH_DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_auth_db(path: Optional[Path] = None) -> None:
    """Create auth tables and seed default accounts if none exist."""
    conn = connect_auth(path)
    try:
        conn.executescript(AUTH_SCHEMA)
        count = conn.execute("SELECT COUNT(*) FROM user").fetchone()[0]
        if count == 0:
            seeds = [
                ("admin", "admin@campaign-intel.pk", "Campaign Admin", "Admin@1234", "admin"),
                ("analyst", "analyst@campaign-intel.pk", "Marketing Analyst", "Analyst@1234", "analyst"),
            ]
            for username, email, full_name, pw, role in seeds:
                conn.execute(
                    """INSERT INTO user (username, email, full_name, password_hash, role)
                       VALUES (?, ?, ?, ?, ?)""",
                    (username, email, full_name, generate_password_hash(pw, method=_PW_METHOD), role),
                )
            conn.commit()
    finally:
        conn.close()


def load_or_create_secret_key(path: Optional[Path] = None) -> str:
    """Load SECRET_KEY from environment or persist a secure random key locally."""
    env_key = os.environ.get("CAMPAIGN_ENGINE_SECRET_KEY") or os.environ.get("SECRET_KEY")
    if env_key and len(env_key) >= 16:
        return env_key
    key_path = Path(path or config.SECRET_KEY_PATH)
    key_path.parent.mkdir(parents=True, exist_ok=True)
    if key_path.exists():
        stored = key_path.read_text(encoding="utf-8").strip()
        if len(stored) >= 32:
            return stored
    fresh = secrets.token_hex(32)
    key_path.write_text(fresh, encoding="utf-8")
    return fresh


# ----------------------------------------------------------------- CSRF & URL safety
def get_csrf_token(session: dict) -> str:
    token = session.get("_csrf_token")
    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token
    return token


def validate_csrf_token(session: dict, token: Optional[str]) -> bool:
    expected = session.get("_csrf_token")
    if not expected or not token:
        return False
    return hmac.compare_digest(str(expected), str(token))


def is_safe_next_url(target: Optional[str]) -> bool:
    if not target:
        return False
    parsed = urlparse(target)
    return not parsed.scheme and not parsed.netloc and target.startswith("/") and not target.startswith("//")


# ----------------------------------------------------------------- validation
def validate_username(username: str) -> Optional[str]:
    u = (username or "").strip()
    if not _USERNAME_RE.match(u):
        return "Username must be 3–30 characters (letters, numbers, ., _, -) and start with a letter or digit."
    return None


def validate_email(email: str) -> Optional[str]:
    e = (email or "").strip()
    if not _EMAIL_RE.match(e) or len(e) > 120:
        return "Please enter a valid email address."
    return None


def validate_password(password: str) -> list[str]:
    errors = []
    if len(password or "") < 8:
        errors.append("at least 8 characters")
    if not re.search(r"[A-Z]", password or ""):
        errors.append("an uppercase letter")
    if not re.search(r"[a-z]", password or ""):
        errors.append("a lowercase letter")
    if not re.search(r"[0-9]", password or ""):
        errors.append("a number")
    if not re.search(r"[^A-Za-z0-9]", password or ""):
        errors.append("a special character")
    return errors


# ----------------------------------------------------------------- audit logging
def log_event(
    event_type: str,
    user_id: Optional[int] = None,
    username: Optional[str] = None,
    ip: str = "",
    ua: str = "",
    details: str = "",
    path: Optional[Path] = None,
) -> None:
    conn = connect_auth(path)
    try:
        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, username, event_type, (ip or "")[:64], (ua or "")[:200], (details or "")[:240]),
        )
        conn.commit()
    finally:
        conn.close()


# ----------------------------------------------------------------- user operations
def _public_user(row: Optional[sqlite3.Row]) -> Optional[dict[str, Any]]:
    if not row:
        return None
    d = dict(row)
    d.pop("password_hash", None)
    name_parts = [p for p in (d.get("full_name") or d.get("username") or "U").split() if p]
    d["initials"] = (name_parts[0][0] + (name_parts[-1][0] if len(name_parts) > 1 else "")).upper()
    return d


def get_user_by_id(user_id: Any, path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    if not user_id:
        return None
    conn = connect_auth(path)
    try:
        row = conn.execute("SELECT * FROM user WHERE user_id = ?", (int(user_id),)).fetchone()
        return _public_user(row)
    except (ValueError, TypeError):
        return None
    finally:
        conn.close()


def register_user(
    username: str,
    email: str,
    full_name: str,
    password: str,
    role: str = "analyst",
    ip: str = "",
    ua: str = "",
    path: Optional[Path] = None,
) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
    username = (username or "").strip()
    email = (email or "").strip().lower()
    full_name = (full_name or "").strip()

    if len(full_name) < 2 or len(full_name) > 80:
        return None, "Full name must be between 2 and 80 characters."
    err = validate_username(username)
    if err:
        return None, err
    err = validate_email(email)
    if err:
        return None, err
    pw_issues = validate_password(password)
    if pw_issues:
        return None, "Password must contain " + ", ".join(pw_issues) + "."
    if role not in ("admin", "analyst", "viewer"):
        role = "analyst"

    conn = connect_auth(path)
    try:
        exists = conn.execute(
            "SELECT username, email FROM user WHERE username = ? OR email = ?",
            (username, email),
        ).fetchone()
        if exists:
            if exists["username"].lower() == username.lower():
                return None, "That username is already taken."
            return None, "An account with that email address already exists."

        pw_hash = generate_password_hash(password, method=_PW_METHOD)
        cur = conn.execute(
            """INSERT INTO user (username, email, full_name, password_hash, role, last_login_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (username, email, full_name, pw_hash, role, _utc_iso()),
        )
        uid = cur.lastrowid
        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, 'register_success', ?, ?, ?)""",
            (uid, username, (ip or "")[:64], (ua or "")[:200], f"New {role} account created"),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM user WHERE user_id = ?", (uid,)).fetchone()
        return _public_user(row), None
    finally:
        conn.close()


def authenticate(
    identifier: str,
    password: str,
    ip: str = "",
    ua: str = "",
    path: Optional[Path] = None,
) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
    ident = (identifier or "").strip()
    if not ident or not password:
        return None, "Please enter both your username/email and password."

    conn = connect_auth(path)
    try:
        row = conn.execute(
            "SELECT * FROM user WHERE username = ? OR email = ?",
            (ident, ident.lower()),
        ).fetchone()

        if not row:
            conn.execute(
                """INSERT INTO auth_audit_log (username, event_type, ip_address, user_agent, details)
                   VALUES (?, 'login_failed', ?, ?, 'Unknown username or email')""",
                (ident[:60], (ip or "")[:64], (ua or "")[:200]),
            )
            conn.commit()
            return None, "Invalid username/email or password."

        uid = row["user_id"]
        uname = row["username"]

        if not row["is_active"]:
            conn.execute(
                """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
                   VALUES (?, ?, 'login_blocked_inactive', ?, ?, 'Deactivated account attempted sign-in')""",
                (uid, uname, (ip or "")[:64], (ua or "")[:200]),
            )
            conn.commit()
            return None, "This account has been deactivated. Contact an administrator."

        locked_dt = _parse_utc(row["locked_until"])
        now = _utc_now()
        if locked_dt and locked_dt > now:
            remaining = max(1, int((locked_dt - now).total_seconds() // 60) + 1)
            conn.execute(
                """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
                   VALUES (?, ?, 'login_blocked_locked', ?, ?, ?)""",
                (uid, uname, (ip or "")[:64], (ua or "")[:200], f"Locked ({remaining} min remaining)"),
            )
            conn.commit()
            return None, f"Account temporarily locked due to repeated failed attempts. Try again in ~{remaining} minute(s)."

        if not check_password_hash(row["password_hash"], password):
            attempts = int(row["failed_attempts"] or 0) + 1
            locked_until = None
            event = "login_failed"
            detail = f"Invalid password (attempt {attempts}/{config.AUTH_LOCKOUT_THRESHOLD})"
            msg = "Invalid username/email or password."

            if attempts >= config.AUTH_LOCKOUT_THRESHOLD:
                locked_until = _utc_iso(now + timedelta(minutes=config.AUTH_LOCKOUT_MINUTES))
                event = "account_locked"
                detail = f"Locked for {config.AUTH_LOCKOUT_MINUTES}m after {attempts} failed attempts"
                msg = (
                    f"Too many failed attempts. Your account is locked for "
                    f"{config.AUTH_LOCKOUT_MINUTES} minutes."
                )

            conn.execute(
                "UPDATE user SET failed_attempts = ?, locked_until = ? WHERE user_id = ?",
                (attempts, locked_until, uid),
            )
            conn.execute(
                """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (uid, uname, event, (ip or "")[:64], (ua or "")[:200], detail),
            )
            conn.commit()
            return None, msg

        conn.execute(
            "UPDATE user SET failed_attempts = 0, locked_until = NULL, last_login_at = ? WHERE user_id = ?",
            (_utc_iso(now), uid),
        )
        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, 'login_success', ?, ?, 'Signed in with verified CAPTCHA')""",
            (uid, uname, (ip or "")[:64], (ua or "")[:200]),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM user WHERE user_id = ?", (uid,)).fetchone()
        return _public_user(updated), None
    finally:
        conn.close()


def update_profile(
    user_id: int,
    full_name: str,
    email: str,
    ip: str = "",
    ua: str = "",
    path: Optional[Path] = None,
) -> Tuple[bool, str]:
    full_name = (full_name or "").strip()
    email = (email or "").strip().lower()
    if len(full_name) < 2 or len(full_name) > 80:
        return False, "Full name must be between 2 and 80 characters."
    err = validate_email(email)
    if err:
        return False, err

    conn = connect_auth(path)
    try:
        conflict = conn.execute(
            "SELECT user_id FROM user WHERE email = ? AND user_id != ?",
            (email, user_id),
        ).fetchone()
        if conflict:
            return False, "That email address is already used by another account."
        user = conn.execute("SELECT username FROM user WHERE user_id = ?", (user_id,)).fetchone()
        if not user:
            return False, "Account not found."
        conn.execute(
            "UPDATE user SET full_name = ?, email = ? WHERE user_id = ?",
            (full_name, email, user_id),
        )
        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, 'profile_updated', ?, ?, 'Profile name/email updated')""",
            (user_id, user["username"], (ip or "")[:64], (ua or "")[:200]),
        )
        conn.commit()
        return True, "Profile updated successfully."
    finally:
        conn.close()


def change_password(
    user_id: int,
    current_password: str,
    new_password: str,
    ip: str = "",
    ua: str = "",
    path: Optional[Path] = None,
) -> Tuple[bool, str]:
    pw_issues = validate_password(new_password)
    if pw_issues:
        return False, "New password must contain " + ", ".join(pw_issues) + "."

    conn = connect_auth(path)
    try:
        row = conn.execute("SELECT username, password_hash FROM user WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            return False, "Account not found."
        if not check_password_hash(row["password_hash"], current_password or ""):
            return False, "Current password is incorrect."
        if check_password_hash(row["password_hash"], new_password):
            return False, "New password must be different from your current password."

        conn.execute(
            "UPDATE user SET password_hash = ? WHERE user_id = ?",
            (generate_password_hash(new_password, method=_PW_METHOD), user_id),
        )
        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, 'password_changed', ?, ?, 'Password updated by user')""",
            (user_id, row["username"], (ip or "")[:64], (ua or "")[:200]),
        )
        conn.commit()
        return True, "Password updated successfully."
    finally:
        conn.close()


def get_recent_audit_logs(
    user_id: Optional[int] = None,
    limit: int = 20,
    path: Optional[Path] = None,
) -> list[dict[str, Any]]:
    conn = connect_auth(path)
    try:
        if user_id is not None:
            rows = conn.execute(
                "SELECT * FROM auth_audit_log WHERE user_id = ? ORDER BY log_id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM auth_audit_log ORDER BY log_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def list_users(path: Optional[Path] = None) -> list[dict[str, Any]]:
    conn = connect_auth(path)
    try:
        rows = conn.execute("SELECT * FROM user ORDER BY user_id ASC").fetchall()
        now = _utc_now()
        out = []
        for r in rows:
            u = _public_user(r)
            ldt = _parse_utc(u.get("locked_until"))
            u["is_locked"] = bool(ldt and ldt > now)
            out.append(u)
        return out
    finally:
        conn.close()


def admin_update_user(
    actor_id: int,
    target_user_id: int,
    action: str,
    role: Optional[str] = None,
    ip: str = "",
    ua: str = "",
    path: Optional[Path] = None,
) -> Tuple[bool, str]:
    conn = connect_auth(path)
    try:
        target = conn.execute("SELECT * FROM user WHERE user_id = ?", (target_user_id,)).fetchone()
        if not target:
            return False, "User not found."

        if action == "toggle_active":
            if target_user_id == actor_id:
                return False, "You cannot deactivate your own account."
            new_state = 0 if target["is_active"] else 1
            conn.execute("UPDATE user SET is_active = ? WHERE user_id = ?", (new_state, target_user_id))
            detail = f"Admin set active={new_state} for {target['username']}"
            msg = f"Account '{target['username']}' {'activated' if new_state else 'deactivated'}."
        elif action == "unlock":
            conn.execute(
                "UPDATE user SET failed_attempts = 0, locked_until = NULL WHERE user_id = ?",
                (target_user_id,),
            )
            detail = f"Admin unlocked {target['username']}"
            msg = f"Account '{target['username']}' unlocked."
        elif action == "set_role" and role in ("admin", "analyst", "viewer"):
            if target_user_id == actor_id and role != "admin":
                return False, "You cannot remove your own administrator role."
            conn.execute("UPDATE user SET role = ? WHERE user_id = ?", (role, target_user_id))
            detail = f"Admin changed role of {target['username']} to {role}"
            msg = f"Updated '{target['username']}' role to {role}."
        else:
            return False, "Unsupported admin action."

        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, 'admin_action', ?, ?, ?)""",
            (actor_id, target["username"], (ip or "")[:64], (ua or "")[:200], detail),
        )
        conn.commit()
        return True, msg
    finally:
        conn.close()


# ----------------------------------------------------------------- user privacy & consent
def get_user_consent(user_id: int, path: Optional[Path] = None) -> Optional[dict[str, Any]]:
    if not user_id:
        return None
    conn = connect_auth(path)
    try:
        row = conn.execute("SELECT * FROM user_consent WHERE user_id = ?", (int(user_id),)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def save_user_consent(
    user_id: int,
    decision: str,
    analytics: bool = False,
    personalization: bool = False,
    diagnostics: bool = False,
    reason: str = "",
    ip: str = "",
    ua: str = "",
    path: Optional[Path] = None,
) -> Tuple[Optional[dict[str, Any]], Optional[str]]:
    if decision not in ("accepted_all", "rejected_all", "custom"):
        return None, "Invalid permission decision."

    if decision == "accepted_all":
        analytics = personalization = diagnostics = True
        default_reason = "Accepted all data processing and analytics permissions."
    elif decision == "rejected_all":
        analytics = personalization = diagnostics = False
        default_reason = "Rejected all optional permissions; strictly essential security cookies only."
    else:
        default_reason = "Saved custom privacy and data processing preferences."

    cleaned_reason = (reason or "").strip()[:300] or default_reason
    now_iso = _utc_iso()

    conn = connect_auth(path)
    try:
        user = conn.execute("SELECT username FROM user WHERE user_id = ?", (int(user_id),)).fetchone()
        if not user:
            return None, "Account not found."

        conn.execute(
            """INSERT INTO user_consent (user_id, decision, essential, analytics, personalization, diagnostics, reason, updated_at)
               VALUES (?, ?, 1, ?, ?, ?, ?, ?)
               ON CONFLICT(user_id) DO UPDATE SET
                   decision = excluded.decision,
                   essential = 1,
                   analytics = excluded.analytics,
                   personalization = excluded.personalization,
                   diagnostics = excluded.diagnostics,
                   reason = excluded.reason,
                   updated_at = excluded.updated_at""",
            (
                int(user_id),
                decision,
                1 if analytics else 0,
                1 if personalization else 0,
                1 if diagnostics else 0,
                cleaned_reason,
                now_iso,
            ),
        )
        scopes = ["essential"]
        if analytics:
            scopes.append("analytics")
        if personalization:
            scopes.append("personalization")
        if diagnostics:
            scopes.append("diagnostics")
        detail = f"{decision} ({', '.join(scopes)}) — Reason: {cleaned_reason}"
        conn.execute(
            """INSERT INTO auth_audit_log (user_id, username, event_type, ip_address, user_agent, details)
               VALUES (?, ?, 'consent_updated', ?, ?, ?)""",
            (int(user_id), user["username"], (ip or "")[:64], (ua or "")[:200], detail[:240]),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM user_consent WHERE user_id = ?", (int(user_id),)).fetchone()
        return dict(row), None
    finally:
        conn.close()
