from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class BuildStatus(Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BuildLog:
    timestamp: datetime
    message: str
    level: str = "info"

    def __str__(self) -> str:
        ts = self.timestamp.strftime("%H:%M:%S")
        return f"[{ts}] [{self.level.upper()}] {self.message}"


@dataclass
class BuildRecord:
    id: str
    package_name: str
    version: str
    architecture: str
    status: BuildStatus = BuildStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    logs: list[BuildLog] = field(default_factory=list)


@dataclass
class RepositoryConfig:
    name: str = ""
    path: str = ""
    description: str = ""
    suites: list[str] = field(default_factory=lambda: ["stable"])
    components: list[str] = field(default_factory=lambda: ["main"])
    architectures: list[str] = field(default_factory=lambda: ["amd64"])
    gpg_key_id: str = ""
    gpg_key_file: str = ""
    origin: str = ""
    label: str = ""
