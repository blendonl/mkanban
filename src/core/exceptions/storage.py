from .base import MKanbanError


class StorageError(MKanbanError):
    pass


class FileOperationError(StorageError):
    pass


class ParseError(StorageError):
    pass