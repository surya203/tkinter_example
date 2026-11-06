"""Four-function calculator with precedence.

The engine is a small state machine over a token list. It never imports
tkinter and never calls eval or exec, so unit tests can run headless.

Display strings use ``+``, ``-``, ``×`` and ``÷``. Results are ``Decimal``
values rendered in fixed-point form, so ``0.1 + 0.2`` shows ``0.3``.
"""

from __future__ import annotations

from decimal import (
    ROUND_HALF_UP,
    Decimal,
    DivisionByZero,
    InvalidOperation,
    localcontext,
)

_OPERATORS = frozenset({"+", "-", "*", "/"})
_OP_DISPLAY = {"+": "+", "-": "-", "*": "×", "/": "÷"}
_MAX_ENTRY_CHARS = 18

_EQUALS_KEYS = frozenset({"=", "enter", "return", "kp_enter", "\r", "\n"})
_CLEAR_KEYS = frozenset({"c", "escape", "esc", "\x1b"})
_BACKSPACE_KEYS = frozenset({"bs", "backspace", "\x08"})


class _CalcError(Exception):
    """A user-facing calculation problem. Callers turn this into ``Error``."""


class CalculatorEngine:
    """Safe ``+ - * /`` calculator.

    Status is one of ``idle``, ``entry``, ``operator``, ``result``, or
    ``error``. Public methods always return the current display and do not
    raise for bad input.
    """

    def __init__(self) -> None:
        self._expr: list[str] = []
        self._entry: str | None = None
        self._result: str | None = None
        self._status = "idle"

    def display(self) -> str:
        """Text currently shown to the user."""
        if self._status == "error":
            return "Error"
        if self._status == "result":
            return self._result or "0"
        if self._status == "idle" or (not self._expr and self._entry is None):
            return "0"
        parts = [_OP_DISPLAY.get(token, token) for token in self._expr]
        if self._entry is not None:
            parts.append(self._entry)
        return " ".join(parts) if parts else "0"

    def clear(self) -> str:
        """Reset to a blank calculator showing ``0``."""
        self._expr = []
        self._entry = None
        self._result = None
        self._status = "idle"
        return self.display()

    def input_digit(self, digit: str) -> str:
        """Append a single digit ``0``-``9`` and return the display."""
        try:
            self._digit(digit)
        except Exception:
            self._fail()
        return self.display()

    def input_decimal(self) -> str:
        """Append a decimal point, or show ``Error`` if the entry already has one."""
        try:
            self._decimal()
        except Exception:
            self._fail()
        return self.display()

    def input_operator(self, operator: str) -> str:
        """Push ``+``, ``-``, ``*`` or ``/``.

        A second operator in a row is ``Error``, except ``-`` after an
        operator, which starts a negative number (``5 × -3``).
        """
        try:
            self._operator(operator)
        except Exception:
            self._fail()
        return self.display()

    def equals(self) -> str:
        """Evaluate the expression. Incomplete input and divide-by-zero show ``Error``."""
        try:
            self._equals()
        except Exception:
            self._fail()
        return self.display()

    def backspace(self) -> str:
        """Delete the last digit or operator. From ``Error``, resets to ``0``."""
        try:
            self._backspace()
        except Exception:
            self._fail()
        return self.display()

    def handle_key(self, key: str) -> str:
        """Apply one keyboard-style key and return the display.

        Accepted keys include digits, ``.``, ``+``, ``-``, ``*``, ``/``,
        ``×``, ``÷``, ``=``, ``Enter``, ``Backspace``, ``Escape`` and ``c``.
        Unknown keys are ignored. Nothing raised by bad input escapes.
        """
        try:
            if not isinstance(key, str) or key == "":
                return self.display()
            if key in {"\r", "\n", "\x08", "\x1b"}:
                raw = {"\r": "=", "\n": "=", "\x08": "BS", "\x1b": "C"}[key]
            else:
                raw = key.strip()
            if raw == "":
                return self.display()
            lowered = raw.lower()
            if lowered in _EQUALS_KEYS or raw in _EQUALS_KEYS:
                return self.equals()
            if lowered in _BACKSPACE_KEYS:
                return self.backspace()
            if lowered in _CLEAR_KEYS:
                return self.clear()
            if raw in {"×", "*"}:
                return self.input_operator("*")
            if raw in {"÷", "/"}:
                return self.input_operator("/")
            if raw in {"−", "-"}:
                return self.input_operator("-")
            if raw == "+":
                return self.input_operator("+")
            if len(raw) == 1 and raw.isdigit():
                return self.input_digit(raw)
            if raw == ".":
                return self.input_decimal()
            return self.display()
        except Exception:
            self._fail()
            return self.display()

    def _fail(self) -> None:
        self._expr = []
        self._entry = None
        self._result = None
        self._status = "error"

    def _start_new_entry(self, text: str) -> None:
        self._expr = []
        self._result = None
        self._entry = text
        self._status = "entry"

    def _digit(self, digit: str) -> None:
        if not isinstance(digit, str) or len(digit) != 1 or not digit.isdigit():
            self._fail()
            return
        if self._status in {"error", "idle", "result"}:
            self._start_new_entry(digit)
            return
        if self._status == "operator":
            self._entry = digit
            self._status = "entry"
            return
        if self._status != "entry" or self._entry is None:
            self._fail()
            return
        if self._entry in {"0", "-0"}:
            if digit == "0":
                return
            self._entry = f"-{digit}" if self._entry.startswith("-") else digit
            return
        if len(self._entry) >= _MAX_ENTRY_CHARS:
            return
        self._entry += digit

    def _decimal(self) -> None:
        if self._status in {"error", "idle", "result"}:
            self._start_new_entry("0.")
            return
        if self._status == "operator":
            self._entry = "0."
            self._status = "entry"
            return
        if self._status != "entry" or self._entry is None:
            self._fail()
            return
        if self._entry == "-":
            self._entry = "-0."
            return
        if "." in self._entry:
            self._fail()
            return
        if len(self._entry) >= _MAX_ENTRY_CHARS:
            return
        self._entry += "."

    def _operator(self, operator: str) -> None:
        if operator not in _OPERATORS:
            self._fail()
            return
        # Stay on Error until the user clears or types a number.
        if self._status == "error":
            return
        if self._status == "operator":
            # 5 × -3: the minus is the sign of the next number, not a second operator.
            if operator == "-":
                self._entry = "-"
                self._status = "entry"
                return
            self._fail()
            return
        if self._status == "idle":
            number = "0"
        elif self._status == "result":
            number = self._result or "0"
            self._result = None
        elif self._status == "entry" and self._entry is not None:
            if not _is_complete_number(self._entry):
                self._fail()
                return
            number = self._entry
            self._entry = None
        else:
            self._fail()
            return
        self._expr.append(number)
        self._expr.append(operator)
        self._status = "operator"

    def _equals(self) -> None:
        if self._status in {"error", "idle", "result"}:
            return
        if self._status != "entry" or self._entry is None:
            self._fail()
            return
        if not _is_complete_number(self._entry):
            self._fail()
            return
        tokens = [*self._expr, self._entry]
        try:
            shown = _format_result(_evaluate(tokens))
        except (
            _CalcError,
            DivisionByZero,
            ZeroDivisionError,
            InvalidOperation,
            ValueError,
        ):
            self._fail()
            return
        self._expr = []
        self._entry = None
        self._result = shown
        self._status = "result"

    def _backspace(self) -> None:
        if self._status == "error":
            self.clear()
            return
        if self._status == "idle":
            return
        if self._status == "result":
            self._entry = self._result or "0"
            self._result = None
            self._expr = []
            self._status = "entry"
        if self._status == "operator":
            if len(self._expr) < 2:
                self.clear()
                return
            self._expr.pop()
            self._entry = self._expr.pop()
            self._status = "entry"
            return
        if self._status != "entry" or self._entry is None:
            self._fail()
            return
        self._entry = self._entry[:-1]
        # A lone "-" is an in-progress negative number. Only a fully deleted
        # entry returns to the previous operator (or to 0).
        if self._entry == "":
            if self._expr:
                self._entry = None
                self._status = "operator"
            else:
                self._entry = None
                self._status = "idle"


def _is_complete_number(text: str) -> bool:
    """True when ``text`` is a finite decimal, not a bare sign or dot."""
    try:
        value = Decimal(text)
    except (InvalidOperation, ValueError):
        return False
    return value.is_finite()


def _evaluate(tokens: list[str]) -> Decimal:
    """Evaluate ``number op number op ...`` with ``*`` and ``/`` before ``+`` and ``-``."""
    if not tokens or len(tokens) % 2 == 0:
        raise _CalcError("incomplete expression")
    with localcontext() as ctx:
        ctx.prec = 28
        ctx.rounding = ROUND_HALF_UP
        ctx.traps[DivisionByZero] = True
        ctx.traps[InvalidOperation] = True
        numbers: list[Decimal] = []
        ops: list[str] = []
        for index, token in enumerate(tokens):
            if index % 2 == 0:
                numbers.append(Decimal(token))
            else:
                if token not in _OPERATORS:
                    raise _CalcError("bad operator")
                ops.append(token)
        index = 0
        while index < len(ops):
            op = ops[index]
            if op not in {"*", "/"}:
                index += 1
                continue
            left = numbers[index]
            right = numbers[index + 1]
            if op == "/":
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                value = left / right
            else:
                value = left * right
            if not value.is_finite():
                raise _CalcError("non-finite")
            numbers[index : index + 2] = [value]
            del ops[index]
        total = numbers[0]
        for op, right in zip(ops, numbers[1:]):
            if op == "+":
                total = total + right
            elif op == "-":
                total = total - right
            else:
                raise _CalcError("unexpected operator")
        if not total.is_finite():
            raise _CalcError("non-finite")
        return total


def _format_result(value: Decimal) -> str:
    """Fixed-point text without binary float noise or a trailing decimal point."""
    if not value.is_finite():
        raise _CalcError("non-finite")
    with localcontext() as ctx:
        ctx.prec = 50
        ctx.rounding = ROUND_HALF_UP
        ctx.traps[InvalidOperation] = True
        rounded = value.quantize(Decimal("1e-12"))
    if not rounded.is_finite() or rounded == 0:
        if rounded == 0:
            return "0"
        raise _CalcError("non-finite")
    text = format(rounded, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-0"}:
        return "0"
    return text
