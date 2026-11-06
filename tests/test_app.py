"""GUI smoke tests. Skipped when tkinter or a display is unavailable."""

from __future__ import annotations

import os
import unittest

try:
    import tkinter as tk

    from calculator.app import CalculatorApp
except ImportError as exc:  # tkinter is optional for the headless engine tests
    tk = None
    CalculatorApp = None
    _IMPORT_ERROR = str(exc)
else:
    _IMPORT_ERROR = ""


def _buttons(widget: tk.Misc) -> list[tk.Button]:
    found: list[tk.Button] = []
    for child in widget.winfo_children():
        if isinstance(child, tk.Button):
            found.append(child)
        found.extend(_buttons(child))
    return found


class GuiSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        if tk is None or CalculatorApp is None:
            self.skipTest(f"tkinter is not installed ({_IMPORT_ERROR})")
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            self.skipTest("no display")
        try:
            self.root = tk.Tk()
        except tk.TclError as exc:
            self.skipTest(f"no display: {exc}")
        self.root.withdraw()
        try:
            self.app = CalculatorApp(self.root)
        except tk.TclError as exc:
            self.root.destroy()
            self.skipTest(f"no display: {exc}")
        self.root.withdraw()
        self.root.update_idletasks()

    def tearDown(self) -> None:
        root = getattr(self, "root", None)
        if root is not None:
            try:
                root.destroy()
            except tk.TclError:
                pass

    def _button(self, text: str) -> tk.Button:
        for button in _buttons(self.root):
            if button.cget("text") == text:
                return button
        self.fail(f"no button labeled {text!r}")
        raise AssertionError

    def test_backspace_button_is_labeled_del(self) -> None:
        labels = {button.cget("text") for button in _buttons(self.root)}
        for text in "0123456789.+-=C":
            self.assertIn(text, labels)
        self.assertIn("×", labels)
        self.assertIn("÷", labels)
        self.assertIn("DEL", labels)
        self.assertNotIn("⌫", labels)
        self.assertNotIn("←", labels)
        self.assertEqual(self._button("DEL").cget("text"), "DEL")

    def test_buttons_evaluate_with_precedence(self) -> None:
        for label in ("2", "+", "3", "×", "4", "="):
            self._button(label).invoke()
        self.assertEqual(self.app.engine.display(), "14")
        self.assertEqual(self.app._display_var.get(), "14")

    def test_keyboard_decimal_divide_by_zero_and_unary_minus(self) -> None:
        self.root.deiconify()
        self.root.update()

        def key(keysym: str) -> None:
            self.root.event_generate("<KeyPress>", keysym=keysym)
            self.root.update()

        for keysym, expected in (
            ("0", "0"),
            ("period", "0."),
            ("1", "0.1"),
            ("plus", "0.1 +"),
            ("0", "0.1 + 0"),
            ("period", "0.1 + 0."),
            ("2", "0.1 + 0.2"),
            ("Return", "0.3"),
        ):
            key(keysym)
            self.assertEqual(self.app.engine.display(), expected)

        self._button("C").invoke()
        self.assertEqual(self.app.engine.display(), "0")

        for label in ("8", "÷", "0", "="):
            self._button(label).invoke()
        self.assertEqual(self.app.engine.display(), "Error")
        self.assertEqual(self.app._display_var.get(), "Error")
        self._button("C").invoke()
        self.assertEqual(self.app.engine.display(), "0")

        for label in ("5", "×", "-", "3", "="):
            self._button(label).invoke()
        self.assertEqual(self.app.engine.display(), "-15")

    def test_backspace_button_deletes_a_digit(self) -> None:
        self._button("1").invoke()
        self._button("2").invoke()
        self._button("DEL").invoke()
        self.assertEqual(self.app.engine.display(), "1")


if __name__ == "__main__":
    unittest.main()
