"""Theme definitions for RSS CLI."""

from __future__ import annotations

from textual.theme import Theme

TOKYO_NIGHT = Theme(
    name="tokyo-night",
    primary="#7aa2f7",
    secondary="#bb9af7",
    accent="#7dcfff",
    warning="#e0af68",
    error="#f7768e",
    success="#9ece6a",
    foreground="#c0caf5",
    background="#1a1b26",
    surface="#1f2335",
    panel="#292e42",
    dark=True,
    variables={
        "input-selection-background": "#7aa2f7 30%",
        "footer-key-foreground": "#7aa2f7",
        "block-cursor-foreground": "#1a1b26",
        "block-cursor-background": "#7aa2f7",
    },
)

NORD = Theme(
    name="nord",
    primary="#88c0d0",
    secondary="#81a1c1",
    accent="#b48ead",
    warning="#ebcb8b",
    error="#bf616a",
    success="#a3be8c",
    foreground="#d8dee9",
    background="#2e3440",
    surface="#3b4252",
    panel="#434c5e",
    dark=True,
    variables={
        "input-selection-background": "#88c0d0 30%",
        "footer-key-foreground": "#88c0d0",
        "block-cursor-foreground": "#2e3440",
        "block-cursor-background": "#88c0d0",
    },
)

CATPPUCCIN = Theme(
    name="catppuccin",
    primary="#cba6f7",
    secondary="#f5c2e7",
    accent="#89dceb",
    warning="#f9e2af",
    error="#f38ba8",
    success="#a6e3a1",
    foreground="#cdd6f4",
    background="#1e1e2e",
    surface="#181825",
    panel="#313244",
    dark=True,
    variables={
        "input-selection-background": "#cba6f7 30%",
        "footer-key-foreground": "#cba6f7",
        "block-cursor-foreground": "#1e1e2e",
        "block-cursor-background": "#cba6f7",
    },
)

THEMES: list[Theme] = [TOKYO_NIGHT, NORD, CATPPUCCIN]
