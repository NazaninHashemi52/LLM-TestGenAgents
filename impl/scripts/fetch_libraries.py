#!/usr/bin/env python3
"""Vendor third-party libraries listed in impl/libraries.json into impl/cut/.

Each entry pins a PyPI package version and wheel hash, and names the single
pure-Python source file to copy. The file is written to impl/cut/<name>.py,
so every generation and evaluation script treats it like any other CUT module.
"""

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

IMPL_DIR = Path(__file__).parent.parent
CUT_DIR = IMPL_DIR / "cut"
REGISTRY = IMPL_DIR / "libraries.json"

_HEADER = (
    "# Vendored from {package}=={version} ({license}) by scripts/fetch_libraries.py.\n"
    "# Do not edit: change impl/libraries.json and re-run the script instead.\n"
)
_REQUIRED_KEYS = ("package", "version", "sha256", "source_file")


def load_libraries(registry: Path = REGISTRY) -> dict:
    """Return the {name: entry} mapping from libraries.json (empty if the file is missing)."""
    if not registry.exists():
        return {}
    libraries = json.loads(registry.read_text())["libraries"]
    for name, entry in libraries.items():
        missing = [k for k in _REQUIRED_KEYS if k not in entry]
        if missing:
            raise ValueError(f"{registry.name}: library '{name}' is missing {missing}")
    return libraries


def _header(entry: dict) -> str:
    return _HEADER.format(**{"license": "see upstream", **entry})


def _download_wheel(entry: dict, dest: Path) -> Path:
    """Download the pinned wheel (hash-checked, no dependencies) into dest."""
    requirements = dest / "requirements.txt"
    requirements.write_text(
        f"{entry['package']}=={entry['version']} --hash=sha256:{entry['sha256']}\n"
    )
    subprocess.run(
        [
            sys.executable, "-m", "pip", "download",
            "--no-deps", "--only-binary", ":all:", "--require-hashes",
            "-r", str(requirements), "-d", str(dest),
        ],
        check=True,
    )
    wheels = list(dest.glob("*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(f"Expected one wheel for {entry['package']}, found {wheels}")
    return wheels[0]


def fetch_library(name: str, entry: dict) -> Path:
    """Download one library and write its source file to impl/cut/<name>.py."""
    with tempfile.TemporaryDirectory() as tmp:
        wheel = _download_wheel(entry, Path(tmp))
        with zipfile.ZipFile(wheel) as zf:
            try:
                source = zf.read(entry["source_file"]).decode("utf-8")
            except KeyError:
                py_files = [n for n in zf.namelist() if n.endswith(".py")]
                raise KeyError(
                    f"'{entry['source_file']}' not in {wheel.name}; available: {py_files}"
                ) from None

    target = CUT_DIR / f"{name}.py"
    # write_bytes keeps upstream line endings (write_text would emit CRLF on Windows)
    target.write_bytes((_header(entry) + source).encode("utf-8"))
    print(f"[fetch] {entry['package']}=={entry['version']} -> {target}")
    return target


def check_library(name: str, entry: dict) -> bool:
    """Return True if impl/cut/<name>.py exists and matches the pinned version."""
    target = CUT_DIR / f"{name}.py"
    if not target.exists():
        print(f"[fetch] MISSING  {name}: {target} not found")
        return False
    if not target.read_text(encoding="utf-8").startswith(_header(entry)):
        print(f"[fetch] STALE    {name}: {target} is not {entry['package']}=={entry['version']}")
        return False
    print(f"[fetch] ok       {name}: {entry['package']}=={entry['version']}")
    return True


def main():
    libraries = load_libraries()

    parser = argparse.ArgumentParser(
        description="Vendor the third-party libraries in libraries.json into impl/cut/"
    )
    parser.add_argument(
        "names",
        nargs="*",
        metavar="NAME",
        help=f"Libraries to fetch (default: all: {', '.join(libraries)})",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only verify the vendored files match libraries.json (no download)",
    )

    args = parser.parse_args()
    names = args.names or list(libraries)
    unknown = [n for n in names if n not in libraries]
    if unknown:
        parser.error(f"unknown library {unknown}; known: {', '.join(libraries)}")

    if args.check:
        ok = all([check_library(n, libraries[n]) for n in names])
        sys.exit(0 if ok else 1)

    for name in names:
        fetch_library(name, libraries[name])


if __name__ == "__main__":
    main()
