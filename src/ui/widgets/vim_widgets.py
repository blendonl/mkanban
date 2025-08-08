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
        return getattr(self, "_vim_mode", VimMode.INSERT)

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
            return

        elif self.vim_mode == VimMode.NORMAL:
            if key == "i":
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "I":
                self.cursor_location = (self.cursor_location[0], 0)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "a":
                row, col = self.cursor_location
                line_length = len(self.get_line(row))
                if col < line_length:
                    self.cursor_location = (row, col + 1)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "A":
                row, _ = self.cursor_location
                line_length = len(self.get_line(row))
                self.cursor_location = (row, line_length)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "o":
                row, _ = self.cursor_location
                self.cursor_location = (row, len(self.get_line(row)))
                self.insert("\n")
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "O":
                row, _ = self.cursor_location
                self.cursor_location = (row, 0)
                self.insert("\n")
                self.cursor_location = (row, 0)
                self.vim_mode = VimMode.INSERT
                event.prevent_default()
            elif key == "h" or key == "left":
                row, col = self.cursor_location
                if col > 0:
                    self.cursor_location = (row, col - 1)
                elif row > 0:
                    prev_line_length = len(self.get_line(row - 1))
                    self.cursor_location = (row - 1, prev_line_length)
                event.prevent_default()
            elif key == "j" or key == "down":
                row, col = self.cursor_location
                if row < self.document.line_count - 1:
                    next_line_length = len(self.get_line(row + 1))
                    new_col = min(col, next_line_length)
                    self.cursor_location = (row + 1, new_col)
                event.prevent_default()
            elif key == "k" or key == "up":
                row, col = self.cursor_location
                if row > 0:
                    prev_line_length = len(self.get_line(row - 1))
                    new_col = min(col, prev_line_length)
                    self.cursor_location = (row - 1, new_col)
                event.prevent_default()
            elif key == "l" or key == "right":
                row, col = self.cursor_location
                line_length = len(self.get_line(row))
                if col < line_length:
                    self.cursor_location = (row, col + 1)
                elif row < self.document.line_count - 1:
                    self.cursor_location = (row + 1, 0)
                event.prevent_default()
            elif key == "0":
                row, _ = self.cursor_location
                self.cursor_location = (row, 0)
                event.prevent_default()
            elif key == "dollar":
                row, _ = self.cursor_location
                line_length = len(self.get_line(row))
                self.cursor_location = (row, line_length)
                event.prevent_default()
            elif key == "w":
                self._move_to_next_word()
                event.prevent_default()
            elif key == "b":
                self._move_to_previous_word()
                event.prevent_default()
            elif key == "G":
                last_row = self.document.line_count - 1
                self.cursor_location = (last_row, 0)
                event.prevent_default()
            elif key == "g":
                if self.last_command == "g":
                    self.cursor_location = (0, 0)
                    self.last_command = None
                else:
                    self.last_command = "g"
                event.prevent_default()
            elif key == "x":
                row, col = self.cursor_location
                line = self.get_line(row)
                if col < len(line):
                    new_line = line[:col] + line[col + 1 :]
                    self.replace_line(row, new_line)
                event.prevent_default()
            elif key == "X":
                row, col = self.cursor_location
                if col > 0:
                    line = self.get_line(row)
                    new_line = line[: col - 1] + line[col:]
                    self.replace_line(row, new_line)
                    self.cursor_location = (row, col - 1)
                event.prevent_default()
            elif key == "d":
                if self.last_command == "d":
                    row, _ = self.cursor_location
                    if self.document.line_count > 1:
                        self.delete_line(row)
                        if row >= self.document.line_count:
                            row = self.document.line_count - 1
                        self.cursor_location = (row, 0)
                    else:
                        self.replace_line(row, "")
                        self.cursor_location = (row, 0)
                    self.last_command = None
                else:
                    self.last_command = "d"
                event.prevent_default()
            elif key == "v":
                self.vim_mode = VimMode.VISUAL
                self.visual_start = self.cursor_location
                event.prevent_default()
            else:
                if key != "g":
                    self.last_command = None
                return

        elif self.vim_mode == VimMode.VISUAL:
            if key == "escape":
                self.vim_mode = VimMode.NORMAL
                self.visual_start = None
                event.prevent_default()
            elif key in ("h", "j", "k", "l", "left", "right", "up", "down"):
                temp_mode = self.vim_mode
                self.vim_mode = VimMode.NORMAL
                self.on_key(event)  # Recursively handle movement
                self.vim_mode = temp_mode
                return
            elif key == "d" or key == "x":
                if self.visual_start is not None:
                    start_row, start_col = self.visual_start
                    end_row, end_col = self.cursor_location

                    if start_row > end_row or (
                        start_row == end_row and start_col > end_col
                    ):
                        start_row, start_col, end_row, end_col = (
                            end_row,
                            end_col,
                            start_row,
                            start_col,
                        )

                    if start_row == end_row:
                        line = self.get_line(start_row)
                        new_line = line[:start_col] + line[end_col + 1 :]
                        self.replace_line(start_row, new_line)
                    else:
                        first_line = self.get_line(start_row)[:start_col]
                        last_line = self.get_line(end_row)[end_col + 1 :]

                        for _ in range(end_row - start_row):
                            self.delete_line(start_row + 1)

                        self.replace_line(start_row, first_line + last_line)

                    self.cursor_location = (start_row, start_col)
                    self.vim_mode = VimMode.NORMAL
                    self.visual_start = None
                event.prevent_default()
            else:
                return

    def _move_to_next_word(self) -> None:
        row, col = self.cursor_location
        line = self.get_line(row)

        while col < len(line) and line[col].isalnum():
            col += 1

        while col < len(line) and line[col].isspace():
            col += 1

        if col >= len(line) and row < self.document.line_count - 1:
            row += 1
            col = 0
            line = self.get_line(row)
            while col < len(line) and line[col].isspace():
                col += 1

        self.cursor_location = (row, min(col, len(line)))

    def _move_to_previous_word(self) -> None:
        row, col = self.cursor_location

        if col > 0:
            col -= 1
        elif row > 0:
            row -= 1
            col = len(self.get_line(row))
            if col > 0:
                col -= 1

        line = self.get_line(row)

        while col > 0 and line[col].isspace():
            col -= 1

        while col > 0 and line[col - 1].isalnum():
            col -= 1

        self.cursor_location = (row, col)
