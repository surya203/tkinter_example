"""Four-function desktop calculator.

Run the GUI with ``python -m calculator``.
``calculator.engine`` performs the arithmetic and does not import tkinter.
"""

from calculator.engine import CalculatorEngine

__all__ = ["CalculatorEngine"]
__version__ = "1.0.0"
