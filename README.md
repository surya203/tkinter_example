# Calculator

A desktop four-function calculator (`+`, `-`, `×`, `÷`) with a tkinter window.
Arithmetic lives in `calculator/engine.py`, which does not import tkinter and does not call `eval` or `exec`, so the tests run without a display.

Multiplication and division happen before addition and subtraction. Operators of the same rank run left to right. Results use `decimal.Decimal`, so `0.1 + 0.2` shows `0.3`.

Divide by zero, a second decimal point in one number, or an operator where a number is required (a second operator in a row, or `=` before the next number) shows `Error`. The window stays open. Press `C`, `Esc`, or `c`, Backspace, or type a digit or `.` to continue.

## Requirements

- Python 3.9 or newer. Verified with Python 3.12.3.
- The standard library only. No third-party packages.
- tkinter, for the GUI. On Debian and Ubuntu:

```bash
sudo apt install python3-tk
```

## Run the app

From the repository root:

```bash
python3 -m calculator
```

`python -m calculator` is the same command when `python` already points at Python 3.

Type with the buttons or the keyboard: digits, `.`, `+`, `-`, `*`, `/`, `Enter` or `=` for equals, Backspace, and `Esc` or `c` for clear.

## Run the tests

From the repository root. This does not open a window:

```bash
python3 -m unittest discover -s tests -v
```
