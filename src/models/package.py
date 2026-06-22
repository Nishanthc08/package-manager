from __future__ import annotations
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class PackageType(Enum):
    BINARY = "binary"
    SOURCE = "source"


class Priority(Enum):
    REQUIRED = "required"
    IMPORTANT = "important"
    STANDARD = "standard"
    OPTIONAL = "optional"
    EXTRA = "extra"


class Section(Enum):
    ADMIN = "admin"
    BASE = "base"
    COMM = "comm"
    DATABASE = "database"
    DEBUG = "debug"
    DEVEL = "devel"
    DOCS = "doc"
    EDITORS = "editors"
    EDUCATION = "education"
    ELECTRONICS = "electronics"
    EMBEDDED = "embedded"
    FONTS = "fonts"
    GAMES = "games"
    GNOME = "gnome"
    GNU_R = "gnu-r"
    GNUSTEP = "gnustep"
    GRAPHICS = "graphics"
    HAMRADIO = "hamradio"
    HASKELL = "haskell"
    HTTPD = "httpd"
    INTERPRETERS = "interpreters"
    INTROSPECTION = "introspection"
    JAVA = "java"
    KDE = "kde"
    KERNEL = "kernel"
    LIBDEVEL = "libdevel"
    LIBS = "libs"
    LISP = "lisp"
    LOCALIZATION = "localization"
    MAIL = "mail"
    MATH = "math"
    MISC = "misc"
    NET = "net"
    NEWS = "news"
    OCAML = "ocaml"
    OLDAPPS = "oldapps"
    OTHERS = "otherosfs"
    PERL = "perl"
    PHP = "php"
    PYTHON = "python"
    RUBY = "ruby"
    RUST = "rust"
    SCIENCE = "science"
    SHELLS = "shells"
    SOUND = "sound"
    TCL = "tcl"
    TEX = "tex"
    TEXT = "text"
    UTILS = "utils"
    VCS = "vcs"
    VIDEO = "video"
    WEB = "web"
    X11 = "x11"
    XFCE = "xfce"
    ZOPE = "zope"


@dataclass
class Dependency:
    package: str
    version: Optional[str] = None
    operator: Optional[str] = None
    alternatives: list[Dependency] = field(default_factory=list)

    def __str__(self) -> str:
        parts = [self.package]
        if self.version and self.operator:
            parts.append(f" ({self.operator} {self.version})")
        result = "".join(parts)
        if self.alternatives:
            result += " | " + " | ".join(str(a) for a in self.alternatives)
        return result


@dataclass
class PackageFile:
    source_path: str
    target_path: str
    permissions: str = "644"
    owner: str = "root"
    group: str = "root"
    is_conf_file: bool = False
    is_executable: bool = False
    is_directory: bool = False


@dataclass
class PackageConfig:
    package_name: str = ""
    version: str = "1.0.0"
    maintainer: str = ""
    email: str = ""
    description: str = ""
    long_description: str = ""
    architecture: str = "amd64"
    section: str = "misc"
    priority: str = "optional"
    essential: bool = False
    homepage: str = ""
    package_type: PackageType = PackageType.BINARY
    source_package: str = ""

    depends: list[Dependency] = field(default_factory=list)
    recommends: list[Dependency] = field(default_factory=list)
    suggests: list[Dependency] = field(default_factory=list)
    pre_depends: list[Dependency] = field(default_factory=list)
    breaks: list[Dependency] = field(default_factory=list)
    conflicts: list[Dependency] = field(default_factory=list)
    provides: list[Dependency] = field(default_factory=list)
    replaces: list[Dependency] = field(default_factory=list)
    built_using: list[Dependency] = field(default_factory=list)

    installed_size: int = 0
    multi_arch: str = "no"

    files: list[PackageFile] = field(default_factory=list)
    conffiles: list[str] = field(default_factory=list)
    dirs: list[str] = field(default_factory=list)

    maintainer_scripts: dict[str, str] = field(default_factory=dict)
    debian_rules: str = ""
    copyright: str = ""
    changelog: str = ""

    def generate_control(self) -> str:
        lines = [
            f"Package: {self.package_name.strip()}",
            f"Version: {self.version.strip()}",
            f"Maintainer: {self.maintainer.strip()} <{self.email.strip()}>" if self.email.strip() else f"Maintainer: {self.maintainer.strip()}",
        ]

        desc = self.description.strip()
        if self.long_description:
            for ld_line in self.long_description.split("\n"):
                desc += "\n " + ld_line
        lines.append(f"Description: {desc}")

        lines.append(f"Architecture: {self.architecture.strip()}")
        lines.append(f"Section: {self.section.strip()}")
        lines.append(f"Priority: {self.priority.strip()}")

        if self.essential:
            lines.append("Essential: yes")
        if self.homepage:
            lines.append(f"Homepage: {self.homepage}")
        if self.installed_size:
            lines.append(f"Installed-Size: {self.installed_size}")
        if self.multi_arch != "no":
            lines.append(f"Multi-Arch: {self.multi_arch}")
        if self.source_package:
            lines.append(f"Source: {self.source_package}")

        dep_fields = [
            ("Depends", self.depends),
            ("Pre-Depends", self.pre_depends),
            ("Recommends", self.recommends),
            ("Suggests", self.suggests),
            ("Breaks", self.breaks),
            ("Conflicts", self.conflicts),
            ("Provides", self.provides),
            ("Replaces", self.replaces),
            ("Built-Using", self.built_using),
        ]
        for field_name, deps in dep_fields:
            if deps:
                lines.append(f"{field_name}: {', '.join(str(d) for d in deps)}")

        return "\n".join(lines) + "\n"

    @property
    def deb_filename(self) -> str:
        return f"{self.package_name}_{self.version}_{self.architecture}.deb"

    @property
    def build_dir(self) -> Path:
        return Path(f"build/{self.package_name}-{self.version}")

    @property
    def debian_dir(self) -> Path:
        return self.build_dir / "DEBIAN"
