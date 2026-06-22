#!/bin/bash
# Boss Package Manager launcher
cd "$(dirname "$0")"
exec /tmp/dpkg-venv/bin/python main.py "$@"
