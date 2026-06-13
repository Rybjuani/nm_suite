from __future__ import annotations

"""
shared/components/base.py
========================
Base mixins and helper classes for NeuroMood UI components.

``ThemeAwareWidgetMixin`` — re-exported from ``shared.theme_qt`` for
convenience.  Prefer importing directly from ``shared.theme_qt`` in
new code.

``NMTokens`` — thin wrapper around ``design_tokens.LIGHT`` /
``design_tokens.DARK`` that provides a cleaner access API::

    tokens = NMTokens(theme='dark')
    tokens.bg('surface')      # → '#141A38'
    tokens.ink('primary')     # → '#ECECFB'
    tokens.color('primary')   # → '#A99CFF'

This is intentionally minimal — for PyQt6 colour objects use the
``v3c()`` helper from ``shared.theme_qt``.
"""

from shared.design_tokens import LIGHT, DARK

# Re-export ThemeAwareWidgetMixin so components can import it from here
# without reaching into theme_qt directly.
try:
    from shared.theme_qt import ThemeAwareWidgetMixin
except ImportError:
    # Graceful fallback when theme_qt is not available (e.g. headless tests)

    class ThemeAwareWidgetMixin:
        """Fallback mixin when theme_qt is unavailable."""

        def _connect_theme(self) -> None:
            pass

        def _apply_theme(self, modo: str) -> None:
            pass


class NMTokens:
    """
    Thin wrapper around design_tokens LIGHT / DARK palettes.

    Provides a cleaner access API than raw dict lookups::

        tokens = NMTokens(theme='dark')
        tokens.bg('surface')      # background key
        tokens.ink('primary')     # text/ink key
        tokens.color('primary')   # any colour key

    Args:
        theme: ``'light'`` or ``'dark'`` (default ``'dark'``).
    """

    __slots__ = ("_t",)

    def __init__(self, theme: str = "dark") -> None:
        self._t: dict[str, str] = LIGHT if theme == "light" else DARK

    def __getitem__(self, key: str) -> str:
        """Raw token lookup; falls back to ``#888888``."""
        return self._t.get(key, "#888888")

    def bg(self, key: str) -> str:
        """Background token. Falls back to ``bg_canvas`` if not found."""
        return self._t.get(f"bg_{key}", self._t.get("bg_canvas", "#888888"))

    def ink(self, key: str) -> str:
        """Ink/text token. Falls back to ``ink_primary`` if not found."""
        return self._t.get(f"ink_{key}", self._t.get("ink_primary", "#888888"))

    def color(self, key: str) -> str:
        """General colour token. Falls back to ``#888888``."""
        return self._t.get(key, "#888888")

    def set_theme(self, theme: str) -> None:
        """Switch the active palette at runtime."""
        self._t = LIGHT if theme == "light" else DARK

    @property
    def theme(self) -> str:
        """Current theme name (``'light'`` or ``'dark'``)."""
        return "light" if self._t is LIGHT else "dark"
