# -*- coding: utf-8 -*-
"""
Template management for welcome messages.

Templates are stored in source/templates/*.txt
Active template name is stored in source/templates/current.txt
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
CURRENT_FILE = TEMPLATES_DIR / "current.txt"


def get_current_template_name() -> str:
    """Get the name of the currently active template."""
    try:
        if CURRENT_FILE.exists():
            name = CURRENT_FILE.read_text(encoding="utf-8").strip()
            if name:
                return name
    except Exception:
        pass
    return "default"


def set_current_template(name: str) -> bool:
    """Set the active template. Returns True if template exists and was set."""
    template_path = TEMPLATES_DIR / f"{name}.txt"
    if not template_path.exists():
        return False
    
    try:
        TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
        CURRENT_FILE.write_text(name, encoding="utf-8")
        return True
    except Exception:
        return False


def list_templates() -> list[str]:
    """List all available template names."""
    if not TEMPLATES_DIR.exists():
        return []
    
    templates = []
    for f in TEMPLATES_DIR.glob("*.txt"):
        if f.name != "current.txt":
            templates.append(f.stem)
    return sorted(templates)


def load_template(name: str | None = None, **format_vars: Any) -> str | None:
    """
    Load a template by name (or current if None).
    
    Supports {placeholder} substitution from format_vars.
    Returns None if template doesn't exist.
    """
    if name is None:
        name = get_current_template_name()
    
    template_path = TEMPLATES_DIR / f"{name}.txt"
    if not template_path.exists():
        return None
    
    try:
        content = template_path.read_text(encoding="utf-8")
        
        # Safe formatting - missing keys become empty string
        class SafeDict(dict):
            def __missing__(self, key):
                return f"{{{key}}}"  # Keep placeholder if not provided
        
        if format_vars:
            content = content.format_map(SafeDict(format_vars))
        
        return content
    except Exception:
        return None


def get_welcome_message(**format_vars: Any) -> str:
    """Get the current welcome message with variables substituted."""
    msg = load_template(None, **format_vars)
    if msg is None:
        return "Привет! Напиши АДМИН, если есть вопросы."
    return msg
