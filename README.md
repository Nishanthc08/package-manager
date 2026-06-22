# Boss Package Manager

[![Build](https://github.com/Nishanthc08/package-manager/actions/workflows/build.yml/badge.svg)](https://github.com/Nishanthc08/package-manager/actions/workflows/build.yml)
[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/Nishanthc08/package-manager/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Ubuntu%20%7C%20Debian-orange.svg)](https://github.com/Nishanthc08/package-manager)

a professional desktop application for building and managing Debian packages — built with Python and PySide6.

built by [Nishanth C](https://github.com/Nishanthc08)

---

## table of contents

- [screenshot](#screenshot)
- [features](#features)
- [install](#install)
- [usage](#usage)
- [building from source](#building-from-source)
- [requirements](#requirements)
- [file structure](#file-structure)
- [contributing](#contributing)
- [license](#license)

---

## screenshot

![Boss Package Manager](https://via.placeholder.com/800x500/1e1e2e/cdd6f4?text=Boss+Package+Manager)

---

## features

- **Package Builder** — visual step-by-step wizard with real-time control file preview, auto-completion, and validation
- **File Manager** — drag-drop file addition, permission editor, visual file tree with conffiles support
- **Build Pipeline** — one-click build with threaded progress, color-coded logs, build history, and install button
- **Package Manager** — browse installed packages, inspect details and file lists, remove packages with one click
- **Repository Manager** — local APT repository creation, GPG signing, Packages.gz and Release metadata generation
- **Template System** — 7 built-in templates (binary, python, systemd, dev libs, web app, kernel, blank), export/import as JSON
- **Syntax Highlighting** — bash highlighting in maintainer scripts, control file highlighting in preview and package info

---

## install

### from release

download the latest release and run:

```bash
pip install PySide6
python main.py
```

### from source

```bash
git clone https://github.com/Nishanthc08/package-manager
cd package-manager
pip install PySide6
python main.py
```

---

## usage

### build a package

1. open the app — `python main.py`
2. go to **Package Builder** — fill in name, version, maintainer, description
3. go to **File Manager** — add files and set permissions
4. go to **Build Pipeline** — click **🔨 Build Package**
5. click **📥 Install** to install the built `.deb`

### manage installed packages

1. go to **Package Manager**
2. search for a package
3. select it to see details and file list
4. click **🗑 Remove Package** to uninstall

### create a repository

1. go to **Repository Manager**
2. set a path, suite, and component
3. click **Initialize Repository**
4. add `.deb` files
5. click **Generate Metadata**

---

## building from source

```bash
git clone https://github.com/Nishanthc08/package-manager
cd package-manager
pip install PySide6
python main.py
```

no build system required — it's a Python script.

---

## requirements

- Ubuntu 20.04+ or any Debian-based system
- Python 3.10+
- PySide6 (`pip install PySide6`)
- `dpkg-deb`, `fakeroot` (for building packages)
- `pkexec` (PolicyKit, for install/remove)

---

## file structure

```
package-manager/
├── main.py                  ← entry point
├── boss-pkg.sh              ← launcher script
├── requirements.txt         ← dependencies
├── LICENSE                  ← MIT license
├── README.md                ← this file
├── CHANGELOG.md             ← version history
├── CONTRIBUTING.md          ← how to contribute
├── CODE_OF_CONDUCT.md       ← community guidelines
├── SECURITY.md              ← security policy
├── SUPPORT.md               ← support info
├── ROADMAP.md               ← planned features
├── src/
│   ├── app.py               ← main window, navigation, menus
│   ├── models/
│   │   ├── package.py       ← PackageConfig, dependency, file models
│   │   └── build.py         ← BuildRecord, build/repo models
│   ├── core/
│   │   ├── dpkg_builder.py  ← build engine (fakeroot + dpkg-deb)
│   │   ├── validator.py     ← control file field validation
│   │   └── templates.py     ← 7 built-in templates
│   ├── widgets/
│   │   ├── wizard.py        ← package builder with syntax highlighting
│   │   ├── file_manager.py  ← drag-drop file manager
│   │   ├── build_pipeline.py ← progress, logs, install button
│   │   ├── package_manager.py ← browse/remove installed packages
│   │   ├── repo_manager.py  ← APT repo with GPG
│   │   └── template_manager.py ← export/import templates
│   └── utils/
│       ├── helpers.py       ← system utilities
│       └── syntax.py        ← bash and control file highlighters
└── .github/
    ├── workflows/
    │   └── build.yml        ← CI pipeline
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## contributing

see [CONTRIBUTING.md](CONTRIBUTING.md) for how to contribute. see [ROADMAP.md](ROADMAP.md) for what is planned.

---

## license

MIT — do whatever you want with it. see [LICENSE](LICENSE).
