"""Self-contained, cryptographically backed server-side SVG CAPTCHA."""
from __future__ import annotations

import hashlib
import hmac
import html
import secrets
import time
from typing import Tuple

from . import config

# Unambiguous alphanumeric characters (omits 0, O, 1, I, L)
ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LENGTH = 6

_LIGHT_PALETTE = ("#0b6e69", "#1d4ed8", "#7c3aed", "#b45309", "#be123c", "#0f766e", "#374151")
_DARK_PALETTE = ("#2dd4bf", "#60a5fa", "#c084fc", "#fbbf24", "#fb7185", "#34d399", "#e2e8f0")


def _hash_answer(answer: str, salt: str) -> str:
    normalized = answer.strip().upper()
    return hashlib.sha256(f"{salt}:{normalized}".encode("utf-8")).hexdigest()


def create_challenge(session: dict, mode: str = "text") -> dict:
    """Create a fresh single-use CAPTCHA challenge and store only its salted hash in session."""
    mode = "math" if mode == "math" else "text"
    rng = secrets.SystemRandom()

    if mode == "math":
        op = rng.choice(["+", "-"])
        if op == "+":
            a = rng.randint(6, 29)
            b = rng.randint(3, 19)
            answer = str(a + b)
        else:
            a = rng.randint(15, 39)
            b = rng.randint(4, a - 3)
            answer = str(a - b)
        display = f"{a} {op} {b} = ?"
    else:
        answer = "".join(secrets.choice(ALPHABET) for _ in range(CODE_LENGTH))
        display = answer

    salt = secrets.token_hex(12)
    session["captcha"] = {
        "id": secrets.token_hex(8),
        "mode": mode,
        "salt": salt,
        "hash": _hash_answer(answer, salt),
        "issued_at": time.time(),
    }
    return {"display": display, "mode": mode}


def verify_challenge(session: dict, user_input: str | None) -> Tuple[bool, str]:
    """Validate and consume the current session CAPTCHA (strictly single-use)."""
    data = session.pop("captcha", None)
    if not data or not isinstance(data, dict):
        return False, "CAPTCHA challenge expired or missing. Please complete the new code."

    issued_at = float(data.get("issued_at", 0))
    if time.time() - issued_at > config.CAPTCHA_TTL_SECONDS:
        return False, "CAPTCHA challenge timed out. Please enter the refreshed code."

    cleaned = (user_input or "").strip()
    if not cleaned:
        return False, "Please complete the CAPTCHA verification."

    expected_hash = str(data.get("hash", ""))
    salt = str(data.get("salt", ""))
    candidate_hash = _hash_answer(cleaned, salt)

    if not expected_hash or not hmac.compare_digest(expected_hash, candidate_hash):
        return False, "Incorrect CAPTCHA answer. Please try the new challenge."

    return True, ""


def render_svg(display_text: str, mode: str = "text", theme: str = "light") -> str:
    """Render a visually rich, anti-OCR SVG CAPTCHA image with zero external dependencies."""
    rng = secrets.SystemRandom()
    dark = theme == "dark"
    w, h = 230, 72

    bg1 = "#111e22" if dark else "#f2f8f7"
    bg2 = "#16292e" if dark else "#e6f2f0"
    grid_col = "rgba(45,212,191,0.09)" if dark else "rgba(11,122,117,0.09)"
    noise_cols = (
        ("rgba(45,212,191,0.28)", "rgba(251,191,36,0.26)", "rgba(129,140,248,0.26)")
        if dark
        else ("rgba(11,122,117,0.24)", "rgba(217,119,6,0.24)", "rgba(79,70,229,0.22)")
    )
    palette = _DARK_PALETTE if dark else _LIGHT_PALETTE
    border_col = "#243b40" if dark else "#cde0dc"

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="Security CAPTCHA challenge">',
        "<defs>",
        f'<linearGradient id="cbg" x1="0%" y1="0%" x2="100%" y2="100%">'
        f'<stop offset="0%" stop-color="{bg1}"/><stop offset="100%" stop-color="{bg2}"/></linearGradient>',
        '<pattern id="cgrid" width="14" height="14" patternUnits="userSpaceOnUse">'
        f'<path d="M 14 0 L 0 0 0 14" fill="none" stroke="{grid_col}" stroke-width="1"/></pattern>',
        "</defs>",
        f'<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="10" fill="url(#cbg)" stroke="{border_col}"/>',
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="9" fill="url(#cgrid)"/>',
    ]

    # Background interference curves
    for _ in range(4):
        x1, y1 = rng.randint(4, 35), rng.randint(8, h - 8)
        cx1, cy1 = rng.randint(50, 110), rng.randint(4, h - 4)
        cx2, cy2 = rng.randint(120, 180), rng.randint(4, h - 4)
        x2, y2 = rng.randint(w - 35, w - 4), rng.randint(8, h - 8)
        col = rng.choice(noise_cols)
        sw = round(rng.uniform(1.1, 2.0), 2)
        parts.append(
            f'<path d="M {x1} {y1} C {cx1} {cy1}, {cx2} {cy2}, {x2} {y2}" '
            f'fill="none" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>'
        )

    # Background noise dots & tiny rings
    for _ in range(28):
        cx = rng.randint(6, w - 6)
        cy = rng.randint(6, h - 6)
        rad = round(rng.uniform(0.9, 2.3), 1)
        col = rng.choice(noise_cols)
        parts.append(f'<circle cx="{cx}" cy="{cy}" r="{rad}" fill="{col}"/>')

    # Characters
    chars = list(display_text) if mode == "text" else display_text.split(" ")
    if mode == "text":
        margin = 20
        step = (w - 2 * margin) / max(len(chars), 1)
        for i, ch in enumerate(chars):
            x = margin + step * i + step * 0.5 + rng.uniform(-3.0, 3.0)
            y = h * 0.56 + rng.uniform(-6.0, 7.0)
            rot = rng.uniform(-20, 20)
            skew = rng.uniform(-8, 8)
            size = rng.randint(25, 30)
            col = rng.choice(palette)
            weight = rng.choice(["700", "800"])
            font = rng.choice(["'Trebuchet MS', sans-serif", "Georgia, serif", "'Segoe UI', sans-serif", "monospace"])
            safe = html.escape(ch)
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'font-family="{font}" font-size="{size}" font-weight="{weight}" fill="{col}" '
                f'transform="rotate({rot:.1f} {x:.1f} {y:.1f}) skewX({skew:.1f})">{safe}</text>'
            )
    else:
        margin = 18
        step = (w - 2 * margin) / max(len(chars), 1)
        for i, token in enumerate(chars):
            x = margin + step * i + step * 0.5 + rng.uniform(-2.0, 2.0)
            y = h * 0.54 + rng.uniform(-5.0, 5.0)
            rot = rng.uniform(-11, 11)
            size = rng.randint(23, 27)
            col = rng.choice(palette)
            safe = html.escape(token)
            parts.append(
                f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" dominant-baseline="central" '
                f'font-family="\'Segoe UI\', system-ui, sans-serif" font-size="{size}" font-weight="800" fill="{col}" '
                f'transform="rotate({rot:.1f} {x:.1f} {y:.1f})">{safe}</text>'
            )

    # Foreground light strikethrough arcs (thin so humans read easily)
    for _ in range(2):
        x1, y1 = rng.randint(8, 30), rng.randint(15, h - 15)
        cx, cy = rng.randint(80, 150), rng.randint(10, h - 10)
        x2, y2 = rng.randint(w - 30, w - 8), rng.randint(15, h - 15)
        col = rng.choice(noise_cols)
        parts.append(
            f'<path d="M {x1} {y1} Q {cx} {cy}, {x2} {y2}" fill="none" stroke="{col}" '
            f'stroke-width="1.4" stroke-dasharray="{rng.randint(4,8)},{rng.randint(3,6)}"/>'
        )

    parts.append("</svg>")
    return "".join(parts)
