import os
import subprocess
import sys
from pathlib import Path

APP_NAME = "Doc Tools"
APP_DIR = "Doc Tools.app"

OFFICE_ROOT = Path(
    os.environ.get("OFFICE_ROOT", Path.home() / "projects/OfficeTools")
)


def _find_local_app() -> Path | None:
    candidate = OFFICE_ROOT / "apps" / APP_DIR
    return candidate if candidate.is_dir() else None


def _register(src: Path) -> bool:
    dst = Path("/Applications") / APP_DIR
    if dst.is_dir():
        result = subprocess.run(["rm", "-rf", str(dst)])
        if result.returncode != 0:
            return False
    result = subprocess.run(["ditto", str(src), str(dst)])
    if result.returncode != 0:
        return False
    subprocess.run(["xattr", "-cr", str(dst)])
    return True


def main() -> None:
    result = subprocess.run(["open", "-a", APP_NAME])
    if result.returncode == 0:
        return

    local = _find_local_app()
    if local:
        if _register(local):
            subprocess.run(["open", "-a", APP_NAME])
            return
        print(f"Failed to copy {APP_DIR}.", file=sys.stderr)
        sys.exit(1)

    print(
        f"{APP_NAME}.app not found.\n"
        f"  ditto 'apps/{APP_DIR}' '/Applications/{APP_DIR}'\n"
        f"  xattr -cr '/Applications/{APP_DIR}'\n"
        f"Then run docgui again.",
        file=sys.stderr,
    )
    sys.exit(1)
