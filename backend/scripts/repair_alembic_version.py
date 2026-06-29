"""
Clear stale rows in alembic_version when the DB references a revision id
that no longer exists under alembic/versions/ (e.g. after a history rewrite).

Run from repo with the backend venv activated (use `python`, not system `python3`):

  cd backend && source .venv/bin/activate
  python scripts/repair_alembic_version.py

Or explicitly:

  backend/.venv/bin/python backend/scripts/repair_alembic_version.py

After running:
  alembic upgrade head

If upgrade fails with "relation ... already exists", your schema is already
applied; use instead:
  alembic stamp 0001_initial_domain_models
"""
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_ROOT))

try:
    from sqlalchemy import create_engine, text  # noqa: E402
except ModuleNotFoundError:  # pragma: no cover
    print(
        "Missing dependencies (sqlalchemy). Use the backend virtualenv Python, not system python3:\n"
        "  cd backend && source .venv/bin/activate && pip install -r requirements.txt\n"
        "  python scripts/repair_alembic_version.py",
        file=sys.stderr,
    )
    sys.exit(1)

from app.config import settings  # noqa: E402


def main() -> None:
    engine = create_engine(settings.DATABASE_URL)
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM alembic_version"))
    print("Cleared alembic_version. Run: alembic upgrade head")
    print(
        "If tables already exist and match the models, use: "
        "alembic stamp 0001_initial_domain_models"
    )


if __name__ == "__main__":
    main()
