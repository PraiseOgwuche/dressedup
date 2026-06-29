"""Fail fast if Python is too new for current dependency wheels (e.g. 3.14)."""
import sys

MIN_SUPPORTED = (3, 11)


def main() -> None:
    v = sys.version_info[:2]
    if v < MIN_SUPPORTED:
        print(
            f"ERROR: Python {v[0]}.{v[1]} is too old. Use Python {MIN_SUPPORTED[0]}.{MIN_SUPPORTED[1]}+.",
            file=sys.stderr,
        )
        sys.exit(1)
    if sys.version_info >= (3, 14):
        print(
            "ERROR: This backend is not installable on Python 3.14+ yet "
            "(psycopg2-binary and pydantic-core need wheels or newer pins).",
            file=sys.stderr,
        )
        print(
            "Fix: use Python 3.12 (recommended) or 3.11:\n"
            "  brew install python@3.12\n"
            "  cd backend && rm -rf .venv && python3.12 -m venv .venv && source .venv/bin/activate\n"
            "  pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
