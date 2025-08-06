"""Vim-enabled input widgets for MKanban."""

from textual.widgets import TextArea
from textual import events


class VimMode:
    NORMAL = "normal"
    INSERT = "insert"


class VimTextArea(TextArea):
    def __init__(self, text="", **kwargs):
        super().__init__(text=text, **kwargs)
        self._vim_mode = VimMode.NORMAL
        self.last_command = None
        self.visual_start = None

    @property
    def vim_mode(self):
        return getattr(self, '_vim_mode', VimMode.INSERT)

    @vim_mode.setter
    def vim_mode(self, value):
        self._vim_mode = value

    def on_key(self, event: events.Key) -> None:
        """Handle vim key bindings."""
        key = event.key

        if self.vim_mode == VimMode.INSERT:
            if key == "escape":
                self.vim_mode = VimMode.NORMAL
                event.prevent_default()
                return
            # Let default TextArea handling work in insert mode
            return

        elif self.vim_mode == VimMode.NORMAL:
            if key == "i":
                # Enter insert mode at cursor
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "I":
                # Enter insert mode at beginning of line
                self.cursor_location = (self.cursor_location[0], 0)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "a":
                # Enter insert mode after cursor
                row, col = self.cursor_location
                line_length = len(self.get_line(row))
                if col < line_length:
                    self.cursor_location = (row, col + 1)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "A":
                # Enter insert mode at end of line
                row, _ = self.cursor_location
                line_length = len(self.get_line(row))
                self.cursor_location = (row, line_length)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "o":
                # Open new line below and enter insert mode
                row, _ = self.cursor_location
                self.cursor_location = (row, len(self.get_line(row)))
                self.insert("\n")
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "O":
                # Open new line above and enter insert mode
                row, _ = self.cursor_location
                self.cursor_location = (row, 0)
                self.insert("\n")
                self.cursor_location = (row, 0)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "h" or key == "left":
                # Move cursor left
                row, col = self.cursor_location
                if col > 0:
                    self.cursor_location = (row, col - 1)
                elif row > 0:
                    prev_line_length = len(self.get_line(row - 1))
                    self.cursor_location = (row - 1, prev_line_length)
                event.prevent_default()
            elif key == "j" or key == "down":
                # Move cursor down
                row, col = self.cursor_location
                if row < self.document.line_count - 1:
                    next_line_length = len(self.get_line(row + 1))
                    new_col = min(col, next_line_length)
                    self.cursor_location = (row + 1, new_col)
                event.prevent_default()
            elif key == "k" or key == "up":
                # Move cursor up
                row, col = self.cursor_location
                if row > 0:
                    prev_line_length = len(self.get_line(row - 1))
                    new_col = min(col, prev_line_length)
                    self.cursor_location = (row - 1, new_col)
                event.prevent_default()
            elif key == "l" or key == "right":
                # Move cursor right
                row, col = self.cursor_location
                line_length = len(self.get_line(row))
                if col < line_length:
                    self.cursor_location = (row, col + 1)
                elif row < self.document.line_count - 1:
                    self.cursor_location = (row + 1, 0)
                event.prevent_default()
            elif key == "0":
                # Move to beginning of line
                row, _ = self.cursor_location
                self.cursor_location = (row, 0)
                event.prevent_default()
            elif key == "dollar":
                # Move to end of line
                row, _ = self.cursor_location
                line_length = len(self.get_line(row))
                self.cursor_location = (row, line_length)
                event.prevent_default()
            elif key == "w":
                # Move to next word
                self._move_to_next_word()
                event.prevent_default()
            elif key == "b":
                # Move to previous word
                self._move_to_previous_word()
                event.prevent_default()
            elif key == "G":
                # Move to last line
                last_row = self.document.line_count - 1
                self.cursor_location = (last_row, 0)
                event.prevent_default()
            elif key == "g":
                # Handle gg (go to first line)
                if self.last_command == "g":
                    self.cursor_location = (0, 0)
                    self.last_command = None
                else:
                    self.last_command = "g"
                event.prevent_default()
            elif key == "x":
                # Delete character under cursor
                row, col = self.cursor_location
                line = self.get_line(row)
                if col < len(line):
                    new_line = line[:col] + line[col + 1:]
                    self.replace_line(row, new_line)
                event.prevent_default()
            elif key == "X":
                # Delete character before cursor
                row, col = self.cursor_location
                if col > 0:
                    line = self.get_line(row)
                    new_line = line[:col - 1] + line[col:]
                    self.replace_line(row, new_line)
                    self.cursor_location = (row, col - 1)
                event.prevent_default()
            elif key == "d":
                # Start delete operation
                if self.last_command == "d":
                    # dd - delete line
                    row, _ = self.cursor_location
                    if self.document.line_count > 1:
                        self.delete_line(row)
                        if row >= self.document.line_count:
                            row = self.document.line_count - 1
                        self.cursor_location = (row, 0)
                    else:
                        # Last line, just clear it
                        self.replace_line(row, "")
                        self.cursor_location = (row, 0)
                    self.last_command = None
                else:
                    self.last_command = "d"
                event.prevent_default()
            elif key == "v":
                # Enter visual mode
                self.vim_mode = VimMode.VISUAL
                self.visual_start = self.cursor_location
                event.prevent_default()
            else:
                # Reset last command for other keys
                if key != "g":
                    self.last_command = None
                return

        elif self.vim_mode == VimMode.VISUAL:
            if key == "escape":
                self.vim_mode = VimMode.NORMAL
                self.visual_start = None
                event.prevent_default()
            elif key in ("h", "j", "k", "l", "left", "right", "up", "down"):
                # Move cursor in visual mode (same as normal mode movement)
                # Reset mode temporarily to reuse normal mode movement
                temp_mode = self.vim_mode
                self.vim_mode = VimMode.NORMAL
                self.on_key(event)  # Recursively handle movement
                self.vim_mode = temp_mode
                return
            elif key == "d" or key == "x":
                # Delete selected text
                if self.visual_start is not None:
                    start_row, start_col = self.visual_start
                    end_row, end_col = self.cursor_location

                    # Ensure start comes before end
                    if (start_row > end_row or
                            (start_row == end_row and start_col > end_col)):
                        start_row, start_col, end_row, end_col = end_row, end_col, start_row, start_col

                    # Delete the selected region
                    if start_row == end_row:
                        # Single line deletion
                        line = self.get_line(start_row)
                        new_line = line[:start_col] + line[end_col + 1:]
                        self.replace_line(start_row, new_line)
                    else:
                        # Multi-line deletion
                        first_line = self.get_line(start_row)[:start_col]
                        last_line = self.get_line(end_row)[end_col + 1:]

                        # Delete lines in between
                        for _ in range(end_row - start_row):
                            self.delete_line(start_row + 1)

                        # Combine first and last parts
                        self.replace_line(start_row, first_line + last_line)

                    self.cursor_location = (start_row, start_col)
                    self.vim_mode = VimMode.NORMAL
                    self.visual_start = None
                event.prevent_default()
            else:
                return

    def _move_to_next_word(self) -> None:
        """Move cursor to the beginning of the next word."""
        row, col = self.cursor_location
        line = self.get_line(row)

        # Skip current word if in middle of one
        while col < len(line) and line[col].isalnum():
            col += 1

        # Skip whitespace
        while col < len(line) and line[col].isspace():
            col += 1

        # If we reached end of line, go to next line
        if col >= len(line) and row < self.document.line_count - 1:
            row += 1
            col = 0
            line = self.get_line(row)
            # Skip leading whitespace on new line
            while col < len(line) and line[col].isspace():
                col += 1

        self.cursor_location = (row, min(col, len(line)))

    def _move_to_previous_word(self) -> None:
        """Move cursor to the beginning of the previous word."""
        row, col = self.cursor_location

        if col > 0:
            col -= 1
        elif row > 0:
            row -= 1
            col = len(self.get_line(row))
            if col > 0:
                col -= 1

        line = self.get_line(row)

        # Skip whitespace
        while col > 0 and line[col].isspace():
            col -= 1

        # Skip to beginning of word
        while col > 0 and line[col - 1].isalnum():
            col -= 1

        self.cursor_location = (row, col)
