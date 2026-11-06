"""GUI smoke tests. Skipped when tkinter or a display is unavailable."""

from __future__ import annotations

import os
import unittest

try:
    import tkinter as tk
    import tkinter.font as tkfont

    from calculator.app import CalculatorApp, visible_text
except ImportError as exc:  # tkinter is optional for the headless engine tests
    tk = None
    tkfont = None
    CalculatorApp = None
    visible_text = None
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


class BackspaceLabelTests(unittest.TestCase):
    def setUp(self) -> None:
        if visible_text is None:
            self.skipTest(f"tkinter is not installed ({_IMPORT_ERROR})")

    def test_zero_width_glyphs_fall_back_to_del(self) -> None:
        def measure(text: str) -> int:
            return 0 if text in {"⌫", "←"} else 20

        self.assertEqual(visible_text(("⌫", "←", "DEL"), measure), "DEL")

    def test_first_drawable_glyph_is_kept(self) -> None:
        self.assertEqual(visible_text(("⌫", "←", "DEL"), lambda text: 8), "⌫")
        self.assertEqual(
            visible_text(("⌫", "←", "DEL"), lambda text: 0 if text == "⌫" else 6),
            "←",
        )

    def test_all_zero_widths_still_use_the_ascii_label(self) -> None:
        self.assertEqual(visible_text(("⌫", "←", "DEL"), lambda text: 0), "DEL")


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

    def test_backspace_label_has_nonzero_width(self) -> None:
        labels = {button.cget("text") for button in _buttons(self.root)}
        for text in "0123456789.+-=C":
            self.assertIn(text, labels)
        self.assertTrue(labels & {"×", "÷"})
        backspace = labels & {"⌫", "←", "DEL"}
        self.assertEqual(len(backspace), 1)
        label = next(iter(backspace))
        button = self._button(label)
        font = tkfont.Font(self.root, font=button.cget("font"))
        self.assertGreater(font.measure(label), 0)
        self.assertGreater(len(label.strip()), 0)

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
        backspace = next(
            button
            for button in _buttons(self.root)
            if button.cget("text") in {"⌫", "←", "DEL"}
        )
        backspace.invoke()
        self.assertEqual(self.app.engine.display(), "1")


if __name__ == "__main__":
    unittest.main()
