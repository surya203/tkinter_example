"""tkinter front end for :class:`calculator.engine.CalculatorEngine`."""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from calculator.engine import CalculatorEngine

_WINDOW_BG = "#d4d4d8"
_DISPLAY_BG = "#111827"
_DISPLAY_FG = "#f9fafb"
_ERROR_FG = "#fca5a5"

# Shown on the backspace key. The first one the button font can draw wins.
# Some Tk builds fall back to "fixed", where Font.measure("⌫") is 0 and the
# button looks blank; "DEL" is ASCII and stays visible there.
_BACKSPACE_LABELS = ("⌫", "←", "DEL")
_BUTTON_FONT = ("DejaVu Sans", 18)
_DISPLAY_FONT = ("DejaVu Sans", 28)

# (label, engine key, row, column, rowspan, colspan, role)
_BUTTONS: tuple[tuple[str, str, int, int, int, int, str], ...] = (
    ("C", "C", 1, 0, 1, 1, "clear"),
    ("⌫", "BS", 1, 1, 1, 1, "back"),
    ("÷", "/", 1, 2, 1, 1, "op"),
    ("×", "*", 1, 3, 1, 1, "op"),
    ("7", "7", 2, 0, 1, 1, "digit"),
    ("8", "8", 2, 1, 1, 1, "digit"),
    ("9", "9", 2, 2, 1, 1, "digit"),
    ("-", "-", 2, 3, 1, 1, "op"),
    ("4", "4", 3, 0, 1, 1, "digit"),
    ("5", "5", 3, 1, 1, 1, "digit"),
    ("6", "6", 3, 2, 1, 1, "digit"),
    ("+", "+", 3, 3, 1, 1, "op"),
    ("1", "1", 4, 0, 1, 1, "digit"),
    ("2", "2", 4, 1, 1, 1, "digit"),
    ("3", "3", 4, 2, 1, 1, "digit"),
    ("=", "=", 4, 3, 2, 1, "equal"),
    ("0", "0", 5, 0, 1, 2, "digit"),
    (".", ".", 5, 2, 1, 1, "digit"),
)

_ROLE_COLORS = {
    "digit": ("#ffffff", "#111827", "#e5e7eb"),
    "op": ("#dbe4ff", "#1e3a8a", "#c7d2fe"),
    "equal": ("#2563eb", "#ffffff", "#1d4ed8"),
    "clear": ("#fee2e2", "#991b1b", "#fecaca"),
    "back": ("#f3f4f6", "#111827", "#e5e7eb"),
}


class CalculatorApp:
    """Window with a display, the four operations, and keyboard bindings."""

    def __init__(self, root: tk.Tk | None = None) -> None:
        self.root = root if root is not None else tk.Tk()
        self.engine = CalculatorEngine()
        self.root.title("Calculator")
        self.root.configure(bg=_WINDOW_BG)
        self.root.minsize(320, 460)
        self.root.geometry("380x540")
        self._display_var = tk.StringVar(value=self.engine.display())
        self._build()
        self._bind_keys()
        self.root.focus_force()

    def _build(self) -> None:
        frame = tk.Frame(self.root, bg=_WINDOW_BG, padx=12, pady=12)
        frame.pack(fill="both", expand=True)
        for column in range(4):
            frame.columnconfigure(column, weight=1, uniform="calc")
        for row in range(1, 6):
            frame.rowconfigure(row, weight=1, uniform="calc")

        self._display = tk.Label(
            frame,
            textvariable=self._display_var,
            anchor="e",
            bg=_DISPLAY_BG,
            fg=_DISPLAY_FG,
            font=_DISPLAY_FONT,
            padx=16,
            pady=20,
            width=14,
        )
        self._display.grid(row=0, column=0, columnspan=4, sticky="nsew", pady=(0, 12))

        backspace_text = visible_text(
            _BACKSPACE_LABELS,
            tkfont.Font(self.root, font=_BUTTON_FONT).measure,
        )
        for label, key, row, column, rowspan, colspan, role in _BUTTONS:
            bg, fg, active = _ROLE_COLORS[role]
            if key == "BS":
                label = backspace_text
            button = tk.Button(
                frame,
                text=label,
                command=lambda k=key: self.press(k),
                font=_BUTTON_FONT,
                bg=bg,
                fg=fg,
                activebackground=active,
                activeforeground=fg,
                relief="flat",
                bd=0,
                highlightthickness=0,
                takefocus=0,
                cursor="hand2",
            )
            button.grid(
                row=row,
                column=column,
                rowspan=rowspan,
                columnspan=colspan,
                sticky="nsew",
                padx=4,
                pady=4,
            )

    def _bind_keys(self) -> None:
        self.root.bind("<Key>", self._on_key)

    def press(self, key: str) -> str:
        """Send one key to the engine, update the display, and return it."""
        try:
            shown = self.engine.handle_key(key)
        except Exception:
            shown = self.engine.clear()
        self._display_var.set(shown)
        self._display.configure(fg=_ERROR_FG if shown == "Error" else _DISPLAY_FG)
        self.root.focus_set()
        return shown

    def _on_key(self, event: tk.Event) -> str | None:
        key = _key_from_event(event)
        if key is None:
            return None
        self.press(key)
        return "break"

    def run(self) -> None:
        """Block in the tkinter main loop."""
        self.root.mainloop()


def visible_text(candidates: tuple[str, ...], measure) -> str:
    """First candidate with a positive width, or the last one if none do.

    ``measure`` is ``tkinter.font.Font.measure``. A missing glyph often
    measures 0, which leaves a button looking empty.
    """
    if not candidates:
        return ""
    for candidate in candidates:
        try:
            width = measure(candidate)
        except tk.TclError:
            width = 0
        if width > 0:
            return candidate
    return candidates[-1]


def _key_from_event(event: tk.Event) -> str | None:
    keysym = event.keysym or ""
    char = event.char or ""
    named = {
        "Return": "=",
        "KP_Enter": "=",
        "BackSpace": "BS",
        "Escape": "C",
        "KP_Add": "+",
        "KP_Subtract": "-",
        "KP_Multiply": "*",
        "KP_Divide": "/",
        "KP_Decimal": ".",
        "plus": "+",
        "minus": "-",
        "asterisk": "*",
        "slash": "/",
        "period": ".",
        "equal": "=",
    }
    if keysym in named:
        return named[keysym]
    if keysym.startswith("KP_") and keysym[3:].isdigit():
        return keysym[3:]
    if len(keysym) == 1 and keysym.isdigit():
        return keysym
    if len(keysym) == 1 and keysym.lower() == "c":
        return "C"
    if char in "0123456789.+-*/=":
        return char
    if char in {"×", "÷"}:
        return char
    if char.lower() == "c":
        return "C"
    return None


def run() -> None:
    """Create the window and run until it is closed."""
    CalculatorApp().run()
