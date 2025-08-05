"""Status bar widget for MKanban."""

from textual.widgets import Static


class StatusBar(Static):
    """Status bar showing current status and key bindings."""
    
    def __init__(self):
        """Initialize status bar."""
        super().__init__()
        self.update_status("Ready")
    
    def update_status(self, message: str) -> None:
        """Update the status message."""
        bindings_text = "q:Quit | n:New | e:Edit | d:Delete | m:Move | p:Parents | s:Save"
        self.update(f"{message} | {bindings_text}")