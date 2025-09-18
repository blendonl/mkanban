#!/usr/bin/env python3

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from infrastructure.cli.commands import main_command

def main():
    main_command()

if __name__ == "__main__":
    main()