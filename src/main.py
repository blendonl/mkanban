#!/usr/bin/env python3

import sys
from pathlib import Path

# Ensure parent directory is in sys.path for both:
# - python -m src.main (already works)
# - python src/main.py (needs this fix)
if __name__ == "__main__":
    parent_dir = Path(__file__).resolve().parent.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from src.infrastructure.cli.commands import main_command


def main():
    main_command()


if __name__ == "__main__":
    main()
