import argparse
import os
import subprocess
import sys
from pathlib import Path

OFFICE_ROOT = Path(
    os.environ.get("OFFICE_ROOT", Path.home() / "Documents/projects/OfficeTools")
)


def _find_tools() -> list[Path]:
    """Find all installable tool directories with [project.scripts]."""
    tools = []
    for entry in sorted(OFFICE_ROOT.iterdir()):
        if not entry.is_dir():
            continue
        toml = entry / "pyproject.toml"
        if not toml.exists():
            continue
        content = toml.read_text()
        if "[project.scripts]" not in content:
            continue
        if entry.name == "officetools":
            continue
        tools.append(entry)
    return tools


def cmd_install(args: argparse.Namespace) -> None:
    tools = _find_tools()
    for tool in tools:
        name = tool.name
        print(f"  {name} ...", end=" ", flush=True)
        try:
            subprocess.run(
                ["uv", "build"],
                capture_output=True,
                text=True,
                check=True,
                cwd=tool,
            )
            wheels = list(tool.glob("dist/*.whl"))
            if not wheels:
                print("FAILED (no wheel)")
                continue
            subprocess.run(
                ["uv", "tool", "install", "--force", str(wheels[0])],
                capture_output=True,
                text=True,
                check=True,
            )
            print("ok")
        except subprocess.CalledProcessError as e:
            print("FAILED")
            print(e.stderr.strip(), file=sys.stderr)


def cmd_update(args: argparse.Namespace) -> None:
    cmd_install(args)


def cmd_list(args: argparse.Namespace) -> None:
    tools = _find_tools()
    for tool in tools:
        toml = tool / "pyproject.toml"
        content = toml.read_text()
        scripts = []
        in_scripts = False
        for line in content.splitlines():
            stripped = line.strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                in_scripts = stripped == "[project.scripts]"
                continue
            if in_scripts and "=" in stripped and not stripped.startswith("#"):
                scripts.append(stripped.split("=")[0].strip())
        print(f"  {tool.name}  ->  {', '.join(scripts)}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="officetools",
        description="Manage all OfficeTools CLI utilities",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("install", help="Install all tools")
    sub.add_parser("update", help="Reinstall all tools (alias for install)")
    sub.add_parser("list", help="List all tools")

    args = parser.parse_args()

    if args.command == "install":
        cmd_install(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "list":
        cmd_list(args)
    else:
        parser.print_help()
