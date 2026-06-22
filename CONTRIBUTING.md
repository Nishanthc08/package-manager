# Contributing to Boss Package Manager

Thanks for wanting to contribute. This project is a desktop application for building and managing Debian packages.

## How to contribute

### Reporting bugs

Open a GitHub issue and include:

- Your OS and version
- What you were doing when the bug happened
- The exact error message or unexpected behavior
- Steps to reproduce

### Feature requests

Open a GitHub issue with "Feature Request" in the title. Describe what you want and why.

### Pull requests

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Test that the app still starts: `python main.py`
5. Open a pull request describing what you changed and why

### Code style

- Follow the existing code style in the project
- PySide6 for all GUI components
- Type hints for all function signatures
- No comments unless something is non-obvious
- Keep methods short and focused

## Development setup

```bash
git clone https://github.com/Nishanthc08/package-manager
cd package-manager
pip install PySide6
python main.py
```
