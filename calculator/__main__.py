"""Entry point for ``python -m calculator``."""

from __future__ import annotations

import sys


def main() -> None:
    try:
        from calculator.app import run
    except ImportError as exc:
        missing = exc.name or ""
        if missing == "tkinter" or "tkinter" in str(exc):
            sys.stderr.write(
                "tkinter is required to open the calculator window.\n"
                "On Linux, install it with: sudo apt install python3-tk\n"
            )
            raise SystemExit(1) from exc
        raise
    run()


if __name__ == "__main__":
    main()
