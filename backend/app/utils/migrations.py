import os
import subprocess


def run_migrations() -> None:
    backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    subprocess.run(["alembic", "upgrade", "head"], cwd=backend_dir, check=True)

