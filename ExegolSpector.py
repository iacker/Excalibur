"""Legacy compatibility entrypoint for ExegolSpector."""

from excalibur.cli import main_legacy


if __name__ == "__main__":
    raise SystemExit(main_legacy())
