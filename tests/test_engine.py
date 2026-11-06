"""Headless tests for the calculator engine. No display and no tkinter."""

from __future__ import annotations

import random
import unittest
from pathlib import Path

from calculator.engine import CalculatorEngine


def _press(sequence: str) -> CalculatorEngine:
    engine = CalculatorEngine()
    for key in sequence:
        if key == " ":
            continue
        engine.handle_key(key)
    return engine


class ArithmeticTests(unittest.TestCase):
    def test_addition_subtraction_multiplication_division(self) -> None:
        cases = {
            "2+3=": "5",
            "10-4=": "6",
            "6*7=": "42",
            "8/2=": "4",
            "1/2=": "0.5",
            "7/2=": "3.5",
            "0/5=": "0",
            "5-5=": "0",
        }
        for sequence, expected in cases.items():
            with self.subTest(sequence=sequence):
                self.assertEqual(_press(sequence).display(), expected)

    def test_precedence_and_left_associativity(self) -> None:
        cases = {
            "2+3*4=": "14",
            "2*3+4=": "10",
            "8/2*2=": "8",
            "8*4/2=": "16",
            "8/4/2=": "1",
            "10-3-2=": "5",
            "20-4*2+6/3=": "14",
            "2+3*4*2=": "26",
            "1+2+3=": "6",
            "1000000*1000000=": "1000000000000",
        }
        for sequence, expected in cases.items():
            with self.subTest(sequence=sequence):
                self.assertEqual(_press(sequence).display(), expected)

    def test_chaining_after_equals_uses_the_result(self) -> None:
        engine = _press("8/2=")
        self.assertEqual(engine.display(), "4")
        self.assertEqual(engine.handle_key("*"), "4 ×")
        self.assertEqual(engine.handle_key("3"), "4 × 3")
        self.assertEqual(engine.handle_key("="), "12")

    def test_digit_after_equals_starts_a_new_expression(self) -> None:
        engine = _press("8/2=")
        self.assertEqual(engine.handle_key("3"), "3")
        self.assertEqual(engine.handle_key("="), "3")

    def test_repeated_equals_keeps_the_result(self) -> None:
        self.assertEqual(_press("2+3==").display(), "5")

    def test_expression_display_uses_operator_symbols(self) -> None:
        engine = CalculatorEngine()
        self.assertEqual(engine.handle_key("2"), "2")
        self.assertEqual(engine.handle_key("+"), "2 +")
        self.assertEqual(engine.handle_key("3"), "2 + 3")
        self.assertEqual(engine.handle_key("*"), "2 + 3 ×")
        self.assertEqual(engine.handle_key("4"), "2 + 3 × 4")
        self.assertEqual(engine.handle_key("="), "14")


class DecimalTests(unittest.TestCase):
    def test_tenths_sum_without_binary_noise(self) -> None:
        self.assertEqual(_press("0.1+0.2=").display(), "0.3")

    def test_typed_trailing_zero_normalizes_on_equals(self) -> None:
        engine = CalculatorEngine()
        for key in "1.50":
            engine.handle_key(key)
        self.assertEqual(engine.display(), "1.50")
        self.assertEqual(engine.equals(), "1.5")

    def test_leading_decimal_point(self) -> None:
        self.assertEqual(_press(".5+.5=").display(), "1")
        self.assertEqual(_press(".25*4=").display(), "1")

    def test_decimal_products_and_differences(self) -> None:
        self.assertEqual(_press("0.1*0.2=").display(), "0.02")
        self.assertEqual(_press("1.25+2.75=").display(), "4")
        self.assertEqual(_press("2.5-3=").display(), "-0.5")
        self.assertEqual(_press("0.10+0.20=").display(), "0.3")

    def test_repeating_division_is_a_fixed_decimal(self) -> None:
        self.assertEqual(_press("1/3=").display(), "0.333333333333")
        self.assertEqual(_press("1/6=").display(), "0.166666666667")

    def test_negative_results(self) -> None:
        self.assertEqual(_press("1-2=").display(), "-1")
        self.assertEqual(_press("3-10+2=").display(), "-5")
        self.assertEqual(_press("0-1/2=").display(), "-0.5")


class ErrorTests(unittest.TestCase):
    def test_divide_by_zero(self) -> None:
        cases = ("8/0=", "0/0=", "5/0*2=", "1+2/0=", "9/0+1=")
        for sequence in cases:
            with self.subTest(sequence=sequence):
                engine = _press(sequence)
                self.assertEqual(engine.display(), "Error")

    def test_repeated_decimal_shows_error(self) -> None:
        engine = CalculatorEngine()
        self.assertEqual(engine.handle_key("1"), "1")
        self.assertEqual(engine.handle_key("."), "1.")
        self.assertEqual(engine.handle_key("2"), "1.2")
        self.assertEqual(engine.handle_key("."), "Error")
        self.assertEqual(_press("..").display(), "Error")
        self.assertEqual(_press("5..2").display(), "2")

    def test_operator_misuse(self) -> None:
        engine = CalculatorEngine()
        engine.handle_key("5")
        self.assertEqual(engine.handle_key("+"), "5 +")
        self.assertEqual(engine.handle_key("+"), "Error")

        engine = CalculatorEngine()
        engine.handle_key("5")
        engine.handle_key("+")
        self.assertEqual(engine.handle_key("="), "Error")

        engine = CalculatorEngine()
        engine.handle_key("4")
        engine.handle_key("*")
        self.assertEqual(engine.handle_key("-"), "Error")

    def test_errors_do_not_raise_and_can_be_cleared(self) -> None:
        engine = _press("8/0=")
        self.assertEqual(engine.display(), "Error")
        self.assertEqual(engine.clear(), "0")
        self.assertEqual(engine.handle_key("2"), "2")
        self.assertEqual(engine.handle_key("+"), "2 +")
        self.assertEqual(engine.handle_key("2"), "2 + 2")
        self.assertEqual(engine.handle_key("="), "4")

    def test_recover_by_typing_a_digit_or_decimal(self) -> None:
        engine = _press("1.2.")
        self.assertEqual(engine.display(), "Error")
        self.assertEqual(engine.handle_key("9"), "9")

        engine = _press("8/0=")
        self.assertEqual(engine.input_decimal(), "0.")
        self.assertEqual(engine.handle_key("5"), "0.5")
        self.assertEqual(engine.equals(), "0.5")

    def test_bad_keys_become_error_instead_of_raising(self) -> None:
        engine = CalculatorEngine()
        self.assertEqual(engine.input_digit("12"), "Error")
        self.assertEqual(engine.input_digit("a"), "Error")
        self.assertEqual(engine.input_operator("%"), "Error")
        self.assertEqual(engine.handle_key("c"), "0")


class EditingTests(unittest.TestCase):
    def test_backspace_deletes_digits_then_stops_at_zero(self) -> None:
        engine = _press("123")
        self.assertEqual(engine.backspace(), "12")
        self.assertEqual(engine.backspace(), "1")
        self.assertEqual(engine.backspace(), "0")
        self.assertEqual(engine.backspace(), "0")

    def test_backspace_removes_operator_then_digits(self) -> None:
        engine = _press("12+")
        self.assertEqual(engine.display(), "12 +")
        self.assertEqual(engine.backspace(), "12")
        self.assertEqual(engine.backspace(), "1")
        self.assertEqual(engine.backspace(), "0")

    def test_backspace_inside_an_expression(self) -> None:
        engine = _press("12+34")
        self.assertEqual(engine.backspace(), "12 + 3")
        self.assertEqual(engine.backspace(), "12 +")
        self.assertEqual(engine.backspace(), "12")

    def test_backspace_on_a_decimal_entry(self) -> None:
        engine = _press("0.5")
        self.assertEqual(engine.backspace(), "0.")
        self.assertEqual(engine.backspace(), "0")
        self.assertEqual(engine.backspace(), "0")

    def test_backspace_edits_a_result(self) -> None:
        engine = _press("12+3=")
        self.assertEqual(engine.display(), "15")
        self.assertEqual(engine.backspace(), "1")
        self.assertEqual(engine.backspace(), "0")

        engine = _press("2+3=")
        self.assertEqual(engine.display(), "5")
        self.assertEqual(engine.backspace(), "0")

        engine = _press("0.1+0.2=")
        self.assertEqual(engine.display(), "0.3")
        self.assertEqual(engine.backspace(), "0.")

    def test_clear_and_keyboard_aliases(self) -> None:
        engine = _press("99")
        self.assertEqual(engine.clear(), "0")
        engine.handle_key("8")
        self.assertEqual(engine.handle_key("c"), "0")
        engine.handle_key("8")
        self.assertEqual(engine.handle_key("C"), "0")
        engine.handle_key("8")
        self.assertEqual(engine.handle_key("Escape"), "0")
        engine.handle_key("8")
        self.assertEqual(engine.handle_key("\x1b"), "0")

    def test_backspace_clears_an_error(self) -> None:
        engine = _press("1/0=")
        self.assertEqual(engine.handle_key("BackSpace"), "0")
        self.assertEqual(engine.handle_key("4"), "4")

    def test_clear_mid_expression_discards_it(self) -> None:
        engine = _press("12+34")
        self.assertEqual(engine.handle_key("C"), "0")
        self.assertEqual(_press("1+1=").display(), "2")
        engine.handle_key("1")
        engine.handle_key("+")
        engine.handle_key("1")
        self.assertEqual(engine.handle_key("="), "2")


class KeyboardTests(unittest.TestCase):
    def test_enter_and_symbols(self) -> None:
        engine = CalculatorEngine()
        for key in ("2", "+", "3", "Enter"):
            engine.handle_key(key)
        self.assertEqual(engine.display(), "5")

        engine = CalculatorEngine()
        self.assertEqual(engine.handle_key("6"), "6")
        self.assertEqual(engine.handle_key("×"), "6 ×")
        self.assertEqual(engine.handle_key("7"), "6 × 7")
        self.assertEqual(engine.handle_key("\n"), "42")

        engine = CalculatorEngine()
        engine.handle_key("9")
        self.assertEqual(engine.handle_key("÷"), "9 ÷")
        engine.handle_key("2")
        self.assertEqual(engine.handle_key("="), "4.5")

    def test_unknown_and_empty_keys_are_ignored(self) -> None:
        engine = _press("4")
        self.assertEqual(engine.handle_key(""), "4")
        self.assertEqual(engine.handle_key("x"), "4")
        self.assertEqual(engine.handle_key("foo"), "4")
        self.assertEqual(engine.handle_key(None), "4")  # type: ignore[arg-type]

    def test_random_key_streams_never_raise(self) -> None:
        keys = list("0123456789.+-*/=") + [
            "BS",
            "C",
            "Enter",
            "Escape",
            "BackSpace",
            "×",
            "÷",
            "c",
            "",
            "nope",
        ]
        rng = random.Random(0)
        for _ in range(40):
            engine = CalculatorEngine()
            for _ in range(80):
                shown = engine.handle_key(rng.choice(keys))
                self.assertIsInstance(shown, str)
                self.assertEqual(shown, engine.display())


class ModuleBoundaryTests(unittest.TestCase):
    def test_engine_source_has_no_tkinter_eval_or_exec(self) -> None:
        import ast

        source = (
            Path(__file__).resolve().parents[1] / "calculator" / "engine.py"
        ).read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: list[str] = []
        called: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.append(node.module or "")
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.append(node.func.id)
        self.assertFalse(any("tkinter" in name for name in imported))
        self.assertNotIn("eval", called)
        self.assertNotIn("exec", called)

    def test_package_import_does_not_import_tkinter(self) -> None:
        import sys

        self.assertNotIn("tkinter", sys.modules)
        import calculator

        self.assertNotIn("tkinter", sys.modules)
        self.assertIs(calculator.CalculatorEngine, CalculatorEngine)


if __name__ == "__main__":
    unittest.main()
