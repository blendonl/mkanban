#!/usr/bin/env python3
"""
MKanban - A Terminal User Interface Kanban Board
"""

import click
from pathlib import Path
from src.app import MKanbanApp


@click.command()
@click.option(
    "--data-dir",
    default="./data",
    help="Directory containing markdown board files",
    type=click.Path(exists=False, path_type=Path),
)
@click.option(
    "--board",
    default=None,
    help="Specific board file to open",
    type=str,
)
def main(data_dir: Path, board: str):
    """Launch MKanban TUI application."""
    app = MKanbanApp(data_dir=data_dir, initial_board=board)
    app.run()


if __name__ == "__main__":
    main()