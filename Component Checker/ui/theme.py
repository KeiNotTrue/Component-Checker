"""Light / dark colour palettes and stylesheet building (Qt Style Sheets)."""
from __future__ import annotations

import re
import tempfile
from pathlib import Path

import qtawesome as qta
from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon, QPixmap

TEMPLATE_PATH = Path(__file__).resolve().parent / "style_template.qss"

PALETTES = {
    "dark": {
        "bg": "#0f1320", "surface": "#171c2e", "surface_alt": "#1f2540", "input_bg": "#12172a",
        "border": "#2b3355", "text": "#e8ebf7", "text_muted": "#9aa4c4",
        "primary": "#7b97ff", "primary_hover": "#96abff", "primary_soft": "#25305c", "primary_text": "#0b1020",
        "ok": "#3ecf8e", "ok_bg": "#13352b",
        "bad": "#ff7a85", "bad_bg": "#3b1c25",
        "warn": "#f5b83d", "warn_bg": "#3a2f13",
        "neutral": "#8a94b8", "neutral_bg": "#222843",
    },
    "light": {
        "bg": "#f3f5fb", "surface": "#ffffff", "surface_alt": "#eef1f9", "input_bg": "#ffffff",
        "border": "#d8ddee", "text": "#1b2238", "text_muted": "#5d6785",
        "primary": "#3556d8", "primary_hover": "#2a46b8", "primary_soft": "#e3e9ff", "primary_text": "#ffffff",
        "ok": "#16895a", "ok_bg": "#e2f6ec",
        "bad": "#cf3347", "bad_bg": "#fde7ea",
        "warn": "#a96a10", "warn_bg": "#fcf0d6",
        "neutral": "#5d6785", "neutral_bg": "#e8ecf6",
    },
}

CATEGORY_ICONS = {
    "cpu": "fa5s.microchip",
    "motherboard": "fa5s.server",
    "ram": "fa5s.memory",
    "gpu": "fa5s.tv",
    "psu": "fa5s.plug",
    "storage": "fa5s.hdd",
    "case": "fa5s.desktop",
}

TONE_ICONS = {
    "ok": "fa5s.check-circle",
    "bad": "fa5s.times-circle",
    "warn": "fa5s.exclamation-triangle",
    "neutral": "fa5s.minus-circle",
}

_settings = QSettings("Component Checker", "Component Checker")
_current = "dark"


def load_saved_theme() -> str:
    global _current
    saved = _settings.value("theme", "dark")
    _current = saved if saved in PALETTES else "dark"
    return _current


def current_name() -> str:
    return _current


def set_theme(name: str) -> None:
    global _current
    _current = name
    _settings.setValue("theme", name)


def palette() -> dict:
    return PALETTES[_current]


def color(token: str) -> str:
    return palette()[token]


def icon(name: str, token: str = "text", active_token: str | None = None) -> QIcon:
    """QtAwesome icon coloured from the current palette (needs a running QApplication)."""
    kwargs = {"color": color(token)}
    if active_token:
        kwargs["color_on"] = color(active_token)
    return qta.icon(name, **kwargs)


def pixmap(name: str, token: str, size: int = 18) -> QPixmap:
    return qta.icon(name, color=color(token)).pixmap(size, size)


def _asset(name: str, icon_name: str, token: str) -> str:
    """Render a small PNG for use inside the stylesheet (combo arrow, check mark)."""
    folder = Path(tempfile.gettempdir()) / "pcmatch_assets"
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}_{_current}.png"
    qta.icon(icon_name, color=color(token)).pixmap(14, 14).save(str(path))
    return path.as_posix()


def build_stylesheet() -> str:
    tokens = dict(palette())
    tokens["arrow_icon"] = _asset("arrow", "fa5s.chevron-down", "text_muted")
    tokens["check_icon"] = _asset("check", "fa5s.check", "primary_text")
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    return re.sub(r"\{\{(\w+)\}\}", lambda m: tokens[m.group(1)], template)
