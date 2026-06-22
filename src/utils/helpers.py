from __future__ import annotations
import os
import re
import subprocess
from pathlib import Path
from typing import Optional


def sanitize_filename(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\-_+.]+", "_", name)


def parse_depends_line(line: str) -> list[dict]:
    deps = []
    for part in line.split(","):
        part = part.strip()
        if not part:
            continue
        alternatives = []
        for alt in part.split("|"):
            alt = alt.strip()
            m = re.match(
                r"^([a-zA-Z0-9][a-zA-Z0-9+\-.]+)\s*(?:\(([<>=!]+)\s+([^)]+)\))?\s*$",
                alt,
            )
            if m:
                alternatives.append(
                    {
                        "package": m.group(1),
                        "operator": m.group(2),
                        "version": m.group(3).strip() if m.group(3) else None,
                    }
                )
        deps.append(alternatives)
    return deps


def format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def run_command(
    cmd: list[str],
    cwd: Optional[str] = None,
    timeout: int = 300,
) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except FileNotFoundError:
        return -1, "", f"Command not found: {cmd[0]}"


def which(cmd: str) -> Optional[str]:
    return shutil.which(cmd)


import shutil


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def copy_with_permissions(src: Path, dst: Path, mode: int = 0o644) -> None:
    shutil.copy2(src, dst)
    os.chmod(dst, mode)


def detect_architecture() -> str:
    try:
        result = subprocess.run(
            ["dpkg", "--print-architecture"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "amd64"


def detect_maintainer() -> tuple[str, str]:
    name = os.environ.get("DEBFULLNAME", "")
    email = os.environ.get("DEBEMAIL", "")
    if not name or not email:
        try:
            result = run_command(["git", "config", "--get", "user.name"])
            if result[0] == 0:
                name = result[1].strip()
            result = run_command(["git", "config", "--get", "user.email"])
            if result[0] == 0:
                email = result[1].strip()
        except Exception:
            pass
    if not name:
        name = os.environ.get("USER", "user")
    if not email:
        email = f"{name}@localhost"
    return name, email
