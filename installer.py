#!/usr/bin/env python3
"""Bootstrap the Cindergrace Argos demo inside a local virtual environment.

Steps performed:
1. Create or reuse the `.venv` folder in the repository root.
2. Install Python dependencies required by the CLI + Flask app.
3. Download and install both English->German and German->English Argos packages.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess  # nosec B404 - Required for installer
import sys
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
VENV_DIR = REPO_ROOT / ".venv"
IS_WINDOWS = os.name == "nt"
LANGUAGE_PAIRS = [
    ("en", "de"),
    ("de", "en"),
]
DEPENDENCIES = ["argostranslate", "gradio", "cindergrace-common"]


def run(command: list[str], **kwargs) -> None:
    """Run a subprocess command and show real-time output."""
    kwargs.setdefault("check", True)
    print(f"[cmd] {' '.join(str(c) for c in command)}")
    subprocess.run(command, **kwargs)  # nosec B603 - Input is controlled


def venv_python() -> Path:
    """Return the path to the python executable inside the virtualenv."""
    script_dir = "Scripts" if IS_WINDOWS else "bin"
    exe_name = "python.exe" if IS_WINDOWS else "python"
    return VENV_DIR / script_dir / exe_name


def ensure_venv(recreate: bool = False) -> None:
    """Create the virtual environment if it does not exist."""
    if recreate and VENV_DIR.exists():
        print("[info] Removing existing virtual environment...")
        shutil.rmtree(VENV_DIR)

    if not VENV_DIR.exists():
        print("[info] Creating virtual environment...")
        run([sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("[info] Virtual environment already exists.")


def install_dependencies() -> None:
    """Install Python dependencies inside the virtual environment."""
    python_bin = venv_python()
    print("[info] Upgrading pip...")
    run([str(python_bin), "-m", "pip", "install", "--upgrade", "pip"])
    print("[info] Installing project dependencies...")
    run([str(python_bin), "-m", "pip", "install", *DEPENDENCIES])


def ensure_language_packages() -> None:
    """Install required Argos Translate language packages."""
    python_bin = venv_python()
    script = textwrap.dedent(
        f"""
        import argostranslate.package

        LANGUAGE_PAIRS = {LANGUAGE_PAIRS!r}

        def ensure_pair(from_code: str, to_code: str) -> None:
            installed = [
                pkg for pkg in argostranslate.package.get_installed_packages()
                if pkg.from_code == from_code and pkg.to_code == to_code
            ]
            human = f"{{from_code}}->{{to_code}}"
            if installed:
                print(f"[info] Argos package {{human}} already installed.")
                return

            print(f"[info] Downloading Argos package {{human}}... this might take a moment.")
            argostranslate.package.update_package_index()
            available = argostranslate.package.get_available_packages()
            try:
                package_to_install = next(
                    pkg for pkg in available
                    if pkg.from_code == from_code and pkg.to_code == to_code
                )
            except StopIteration as exc:
                raise RuntimeError(f"Could not find {{human}} package in package index.") from exc
            argostranslate.package.install_from_path(package_to_install.download())
            print(f"[info] Argos package {{human}} installed.")

        for from_code, to_code in LANGUAGE_PAIRS:
            ensure_pair(from_code, to_code)
        """
    ).strip()

    run([str(python_bin), "-c", script])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Set up the local Cindergrace Argos virtual environment."
    )
    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Delete and recreate the virtual environment before installing.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_venv(recreate=args.recreate)
    install_dependencies()
    ensure_language_packages()
    print(
        "\n[done] Setup complete. The start script will now launch the application.\n"
    )


if __name__ == "__main__":
    main()
