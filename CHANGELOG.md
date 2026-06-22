# Changelog

All notable changes to Boss Package Manager are listed here.
Format follows https://keepachangelog.com


## [1.0] - 2026-06-22

First release.

### Added

- Visual Package Builder with tabbed form, auto-completion, and control file preview
- File Manager with filesystem browser, drag-drop file addition, and permission editor
- Build Pipeline with real-time progress bar, color-coded logs, and build history table
- Package Manager to browse, inspect, and remove installed Debian packages
- Repository Manager for local APT repos with GPG signing and Packages.gz generation
- Template system with 7 built-in templates (binary, python, systemd, dev libs, web app, kernel, blank)
- Import/export of package templates as JSON
- Bash syntax highlighting in maintainer script editors
- Control file syntax highlighting in preview
- One-click install of built packages via PolicyKit (pkexec)
- Integrated remove button in Package Manager with pkexec dpkg --purge
