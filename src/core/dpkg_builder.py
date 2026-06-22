from __future__ import annotations
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from src.models.package import PackageConfig
from src.models.build import BuildRecord, BuildStatus, BuildLog
from src.utils.helpers import ensure_dir, run_command


class DPKGBuilder:
    def __init__(self, config: PackageConfig, build_dir: str = "/tmp/package-manager"):
        self.config = config
        self.base_dir = Path(build_dir)
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    def build(self, progress_callback: Optional[Callable] = None,
              log_callback: Optional[Callable] = None) -> BuildRecord:
        record = BuildRecord(
            id=datetime.now().strftime("%Y%m%d%H%M%S"),
            package_name=self.config.package_name,
            version=self.config.version,
            architecture=self.config.architecture,
            status=BuildStatus.RUNNING,
            started_at=datetime.now(),
        )
        self._cancelled = False

        def log(msg: str, level: str = "info"):
            entry = BuildLog(timestamp=datetime.now(), message=msg, level=level)
            record.logs.append(entry)
            if log_callback:
                log_callback(entry)

        def progress(pct: int, msg: str):
            if progress_callback:
                progress_callback(pct, msg)

        try:
            for tool in ["dpkg-deb", "fakeroot"]:
                if not shutil.which(tool):
                    raise RuntimeError(f"Required tool not found: {tool}")

            package_dir = self.base_dir / f"{self.config.package_name}-{self.config.version}"
            debian_dir = package_dir / "DEBIAN"

            log("Cleaning build directory...")
            if package_dir.exists():
                shutil.rmtree(package_dir)
            progress(5, "Cleaning build directory")

            log(f"Creating package structure at {package_dir}...")
            ensure_dir(debian_dir)
            progress(10, "Creating package structure")

            if self._cancelled:
                raise KeyboardInterrupt()

            log("Generating control file...")
            control_content = self.config.generate_control()
            control_path = debian_dir / "control"
            control_path.write_text(control_content)
            progress(20, "Generating control file")

            if self._cancelled:
                raise KeyboardInterrupt()

            log("Writing maintainer scripts...")
            script_names = {
                "preinst": "preinst",
                "postinst": "postinst",
                "prerm": "prerm",
                "postrm": "postrm",
            }
            for script_name, filename in script_names.items():
                content = self.config.maintainer_scripts.get(script_name, "")
                if content:
                    script_path = debian_dir / filename
                    script_path.write_text(content)
                    script_path.chmod(0o755)
            progress(30, "Writing maintainer scripts")

            if self.config.conffiles:
                log("Writing conffiles...")
                conffiles_path = debian_dir / "conffiles"
                conffiles_path.write_text("\n".join(self.config.conffiles) + "\n")
            progress(35, "Writing conffiles")

            if self._cancelled:
                raise KeyboardInterrupt()

            log("Copying package files...")
            total_files = len(self.config.files)
            for idx, pkg_file in enumerate(self.config.files):
                if self._cancelled:
                    raise KeyboardInterrupt()

                if pkg_file.is_directory:
                    target = package_dir / pkg_file.target_path.lstrip("/")
                    ensure_dir(target)
                else:
                    source = Path(pkg_file.source_path)
                    target = package_dir / pkg_file.target_path.lstrip("/")
                    ensure_dir(target.parent)
                    if source.exists():
                        shutil.copy2(source, target)
                        perm = int(pkg_file.permissions, 8) if pkg_file.permissions else 0o644
                        target.chmod(perm)
                    else:
                        log(f"Source file not found: {source}", "warning")

                if total_files > 0:
                    pct = 35 + int((idx + 1) / total_files * 25)
                    progress(pct, f"Copying files ({idx + 1}/{total_files})")

            if self._cancelled:
                raise KeyboardInterrupt()

            log("Setting directory permissions...")
            if self.config.dirs:
                for d in self.config.dirs:
                    dir_path = package_dir / d.lstrip("/")
                    ensure_dir(dir_path)
            progress(65, "Setting directory permissions")

            deb_output = self.base_dir / self.config.deb_filename

            if self._cancelled:
                raise KeyboardInterrupt()

            log("Building .deb package with dpkg-deb...")
            progress(70, "Building .deb package")
            log(f"Running: fakeroot dpkg-deb --build {package_dir} {deb_output}")

            result = run_command(
                ["fakeroot", "dpkg-deb", "--build", str(package_dir), str(deb_output)],
                timeout=600,
            )

            if result[0] != 0:
                error_msg = result[2] if result[2] else result[1]
                raise RuntimeError(f"dpkg-deb failed: {error_msg}")

            log(f"Package built: {deb_output}")
            progress(90, f"Package built: {self.config.deb_filename}")

            if self._cancelled:
                raise KeyboardInterrupt()

            log("Verifying package...")
            run_command(
                ["dpkg-deb", "--info", str(deb_output)],
                timeout=30,
            )
            progress(95, "Verifying package")

            record.status = BuildStatus.SUCCESS
            record.output_path = str(deb_output)
            log(f"Build complete: {deb_output}", "success")

        except KeyboardInterrupt:
            record.status = BuildStatus.CANCELLED
            record.error_message = "Build cancelled by user"
            log("Build cancelled by user", "warning")

        except Exception as e:
            record.status = BuildStatus.FAILED
            record.error_message = str(e)
            log(f"Build failed: {e}", "error")

        finally:
            record.completed_at = datetime.now()
            progress(100, "Done")

        return record
