from __future__ import annotations

from src.models.package import PackageConfig, Dependency, Section


TEMPLATES: dict[str, PackageConfig] = {}


def _build_templates():
    t = TEMPLATES

    t["simple-binary"] = PackageConfig(
        package_name="myapp",
        version="1.0.0",
        description="Simple application package",
        long_description="A simple binary package with basic structure.",
        section=Section.MISC.value,
        priority=Priority.OPTIONAL.value,
        architecture="amd64",
        depends=[Dependency(package="libc6 (>= 2.31)")],
    )

    t["python-library"] = PackageConfig(
        package_name="python3-mylib",
        version="1.0.0",
        description="Python 3 library package",
        long_description="A Python 3 library packaged as a Debian binary.",
        section=Section.PYTHON.value,
        priority=Priority.OPTIONAL.value,
        architecture="all",
        depends=[
            Dependency(package="python3"),
            Dependency(package="python3-requests"),
        ],
    )

    t["system-service"] = PackageConfig(
        package_name="myservice",
        version="1.0.0",
        description="System service daemon",
        long_description="A system service that runs as a daemon using systemd.",
        section=Section.ADMIN.value,
        priority=Priority.OPTIONAL.value,
        architecture="amd64",
        depends=[
            Dependency(package="systemd"),
            Dependency(package="adduser"),
        ],
        dirs=["/etc/myservice", "/var/log/myservice", "/var/lib/myservice"],
    )

    t["library-dev"] = PackageConfig(
        package_name="libfoo-dev",
        version="1.0.0",
        description="Foo library development files",
        long_description="Headers and static libraries for the Foo library.",
        section=Section.LIBDEVEL.value,
        priority=Priority.OPTIONAL.value,
        architecture="amd64",
        depends=[
            Dependency(package="libfoo1", operator="=", version="1.0.0"),
        ],
    )

    t["web-application"] = PackageConfig(
        package_name="mywebapp",
        version="1.0.0",
        description="Web application package",
        long_description="A web application served by a web server.",
        section=Section.WEB.value,
        priority=Priority.OPTIONAL.value,
        architecture="all",
        depends=[
            Dependency(package="apache2"),
            Dependency(package="php"),
        ],
    )

    t["kernel-module"] = PackageConfig(
        package_name="my-module-dkms",
        version="1.0.0",
        description="Kernel module package (DKMS)",
        long_description="A kernel module built with DKMS framework.",
        section=Section.KERNEL.value,
        priority=Priority.OPTIONAL.value,
        architecture="amd64",
        depends=[
            Dependency(package="dkms"),
        ],
    )

    t["empty"] = PackageConfig(
        package_name="",
        version="1.0.0",
        description="",
        section=Section.MISC.value,
        priority=Priority.OPTIONAL.value,
        architecture="amd64",
    )


from src.models.package import Priority

_build_templates()


def get_template(name: str) -> PackageConfig | None:
    from copy import deepcopy

    if name in TEMPLATES:
        return deepcopy(TEMPLATES[name])
    return None


def list_templates() -> list[str]:
    return list(TEMPLATES.keys())


def get_template_description(name: str) -> str:
    if name in TEMPLATES:
        cfg = TEMPLATES[name]
        return f"{cfg.description} ({cfg.architecture})"
    return ""
