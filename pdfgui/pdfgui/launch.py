import subprocess
import sys
from pathlib import Path

APP_NAME = "PDF Tools"
APP_DIR = "Pdf Tools.app"


def _find_local_app() -> Path | None:
    repo = Path(__file__).resolve().parent.parent.parent
    candidate = repo / "apps" / APP_DIR
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
        answer = (
            input(f"{APP_NAME}.app not registered. Copy to /Applications? [Y/n] ")
            .strip()
            .lower()
        )
        if answer in ("", "y", "yes"):
            if _register(local):
                subprocess.run(["open", "-a", APP_NAME])
                return
            print(f"Failed to copy {APP_DIR}.", file=sys.stderr)
            sys.exit(1)

    print(
        f"{APP_NAME}.app not found.\n"
        f"  ditto 'apps/{APP_DIR}' '/Applications/{APP_DIR}'\n"
        f"  xattr -cr '/Applications/{APP_DIR}'\n"
        f"Then run pdfgui again.",
        file=sys.stderr,
    )
    sys.exit(1)
