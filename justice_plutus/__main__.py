"""Module entrypoint for `python -m justice_plutus`."""

from .cli import main


if __name__ == "__main__":
    raise SystemExit(main())
