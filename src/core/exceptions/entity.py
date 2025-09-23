from .base import MKanbanError


class ItemNotFoundError(MKanbanError):
    pass


class ColumnNotFoundError(MKanbanError):
    pass


class BoardNotFoundError(MKanbanError):
    pass