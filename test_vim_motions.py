#!/usr/bin/env python3
"""Test script for vim motions in MKanban."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from textual.app import App
from textual.containers import Vertical
from textual.widgets import Label
from ui.vim_widgets import VimInput, VimTextArea


class VimTestApp(App):
    """Test app for vim widgets."""
    
    def compose(self):
        """Compose the test layout."""
        with Vertical():
            yield Label("Test VimInput (press 'i' to enter insert mode, 'escape' for normal mode):")
            yield VimInput(placeholder="Type here and test vim motions", id="vim_input")
            
            yield Label("Test VimTextArea (starts in insert mode, 'escape' for normal mode):")
            yield VimTextArea("# Test Document\n\nThis is a test.\nTry vim motions like h,j,k,l, w, b, 0, $, gg, G\n\nPress 'i' for insert mode, 'a' for append, 'o' for new line.", id="vim_textarea")
    
    def on_mount(self):
        """Focus the input on startup."""
        self.query_one("#vim_input").focus()


if __name__ == "__main__":
    app = VimTestApp()
    app.run()