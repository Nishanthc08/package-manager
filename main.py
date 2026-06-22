#!/usr/bin/env python3
"""
Boss Package Manager - Professional Debian Package Manager Desktop App

A feature-rich desktop application for building, managing, and
distributing Debian packages with an intuitive graphical interface.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.app import run

if __name__ == "__main__":
    run()
