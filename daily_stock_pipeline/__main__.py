"""Module entrypoint for `python -m daily_stock_pipeline`."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
