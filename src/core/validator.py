from __future__ import annotations
import re
from typing import Optional


class ValidationResult:
    def __init__(self):
        self.errors: list[dict] = []
        self.warnings: list[dict] = []

    def add_error(self, field: str, message: str) -> None:
        self.errors.append({"field": field, "message": message})

    def add_warning(self, field: str, message: str) -> None:
        self.warnings.append({"field": field, "message": message})

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0

    def merge(self, other: ValidationResult) -> None:
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)


_package_name_re = re.compile(r"^[a-z0-9][a-z0-9+\-.]+$")
_version_re = re.compile(r"^(\d+:)?[0-9a-zA-Z.+~-]+$")
_email_re = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_package_name(name: str) -> Optional[str]:
    if not name:
        return "Package name is required"
    if len(name) < 2:
        return "Package name must be at least 2 characters"
    if len(name) > 64:
        return "Package name must be 64 characters or fewer"
    if not _package_name_re.match(name):
        return "Package name must start with a lowercase letter or digit, and contain only a-z, 0-9, +, -, ."
    return None


def validate_version(version: str) -> Optional[str]:
    if not version:
        return "Version is required"
    if not _version_re.match(version):
        return "Invalid version format"
    if len(version) > 64:
        return "Version must be 64 characters or fewer"
    return None


def validate_email(email: str) -> Optional[str]:
    if not email:
        return "Email is required"
    if not _email_re.match(email):
        return "Invalid email format"
    return None


def validate_maintainer(maintainer: str) -> Optional[str]:
    if not maintainer:
        return "Maintainer name is required"
    if len(maintainer) < 2:
        return "Maintainer name must be at least 2 characters"
    return None


def validate_description(description: str) -> Optional[str]:
    if not description:
        return "Description is required"
    if len(description) < 10:
        return "Description should be at least 10 characters"
    return None


def validate_architecture(arch: str) -> Optional[str]:
    valid = {"all", "amd64", "i386", "arm64", "armhf", "armel", "mips64el", "ppc64el", "s390x", "riscv64"}
    if arch not in valid:
        return f"Unknown architecture: {arch}"
    return None


def validate_config(config) -> ValidationResult:
    result = ValidationResult()

    err = validate_package_name(config.package_name)
    if err:
        result.add_error("package_name", err)

    if not config.maintainer:
        result.add_error("maintainer", "Maintainer name is required")

    if not config.email:
        result.add_warning("email", "Email is recommended for Maintainer field")
    else:
        err = validate_email(config.email)
        if err:
            result.add_error("email", err)

    err = validate_version(config.version)
    if err:
        result.add_error("version", err)

    err = validate_description(config.description)
    if err:
        result.add_warning("description", err)

    if config.package_type.value == "binary" and not config.files:
        result.add_warning("files", "No files added to package")

    return result
