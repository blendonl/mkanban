#!/usr/bin/env python3
"""Minimal test for vim widgets."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from textual.app import App
from textual.containers import Vertical

# Test the vim widgets directly
try:
    from ui.vim_widgets import VimInput, VimTextArea, VimMode
    print("Imports successful")
    
    # Test creating the widgets
    vim_input = VimInput(placeholder="test")
    vim_textarea = VimTextArea("test content")
    
    print("Widget creation successful")
    print(f"VimInput mode: {vim_input.vim_mode}")
    print(f"VimTextArea mode: {vim_textarea.vim_mode}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()