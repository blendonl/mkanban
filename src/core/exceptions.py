class MKanbanError(Exception):
    pass


class StorageError(MKanbanError):
    pass


class ValidationError(MKanbanError):
    pass


class ItemNotFoundError(MKanbanError):
    pass


class ColumnNotFoundError(MKanbanError):
    pass


class BoardNotFoundError(MKanbanError):
    pass


class FileOperationError(StorageError):
    pass


class ParseError(StorageError):
    pass


class ConfigurationError(MKanbanError):
    pass
